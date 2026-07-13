from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.models import PolicyDocument
from app.repositories.policy_repository import PolicyRepository
from app.schemas import PolicyPipelineRequest, PolicyPipelineResponse
from app.services.ingestion import PolicyPipelineService


@dataclass(slots=True)
class FileValidationResult:
    source_path: str
    status: str
    mode: str
    policy_name_guess: str | None
    policy_name_resolved: str | None
    version_label: str | None
    parse_method: str | None
    suspected_scanned: bool | None
    ocr_stage_status: str | None
    ocr_message: str | None
    ocr_failed_blocks: int
    text_length: int
    section_count: int
    chunk_count: int
    persisted: bool
    requested_target_document_id: int | None
    document_id: int | None
    version_id: int | None
    error: str | None
    raw_text_preview: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量执行制度入库验证脚本，直接复用正式入库流水线。"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="待验证的 PDF/DOCX 文件列表。",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="可选：每行一个文件路径的清单文件。",
    )
    parser.add_argument(
        "--mode",
        choices=("preview", "ingest"),
        default="ingest",
        help="验证模式：preview 只跑流水线不落库；ingest 跑完整落库。",
    )
    parser.add_argument(
        "--policy-category",
        default="管理制度",
        help="制度分类，默认写入“管理制度”。",
    )
    parser.add_argument(
        "--responsible-department",
        default=None,
        help="可选：责任部门。",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="可选：输出目录。默认写入 scripts/ocr/output/<时间戳>/",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="遇到首个失败文件后立即停止。",
    )
    parser.add_argument(
        "--policy-name-override",
        default=None,
        help="可选：显式指定制度名称，用于版本归并。",
    )
    parser.add_argument(
        "--chain-versions",
        action="store_true",
        help="将本次批量文件串成同一个 document 的版本链。",
    )
    parser.add_argument(
        "--reverse-input",
        action="store_true",
        help="按给定顺序的反向处理输入文件。",
    )
    return parser.parse_args()


def load_input_files(args: argparse.Namespace) -> list[Path]:
    files: list[str] = list(args.files)
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest_lines = manifest_path.read_text(encoding="utf-8").splitlines()
        files.extend(line.strip() for line in manifest_lines if line.strip())

    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw_path in files:
        path = Path(raw_path).expanduser().resolve()
        if path in seen:
            continue
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{path}")
        if not path.is_file():
            raise IsADirectoryError(f"路径不是文件：{path}")
        resolved.append(path)
        seen.add(path)

    if not resolved:
        raise ValueError("未提供任何待验证文件。")
    if args.reverse_input:
        resolved.reverse()
    return resolved


def build_output_dir(output_dir: str | None) -> Path:
    if output_dir:
        target = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = Path("scripts/ocr/output").resolve() / stamp
    target.mkdir(parents=True, exist_ok=True)
    return target


def run_pipeline_for_file(
    *,
    source_path: Path,
    mode: str,
    policy_category: str,
    responsible_department: str | None,
    target_document_id: int | None,
) -> PolicyPipelineResponse:
    request = PolicyPipelineRequest(
        source_path=str(source_path),
        policy_category=policy_category,
        responsible_department=responsible_department,
        target_document_id=target_document_id,
    )

    if mode == "preview":
        service = PolicyPipelineService()
        return service.preview(request)

    session = SessionLocal()
    try:
        repository = PolicyRepository(session)
        service = PolicyPipelineService(repository=repository)
        return service.ingest(request)
    finally:
        session.close()


def extract_file_result(
    response: PolicyPipelineResponse,
    *,
    mode: str,
    target_policy_name: str | None,
) -> FileValidationResult:
    failed_stage = next((stage for stage in response.stages if stage.status == "failed"), None)
    ocr_stage = next((stage for stage in response.stages if stage.stage == "ocr_processing"), None)
    parsed_text = response.parsed_text
    persistence = response.persistence
    section_result = response.section_result
    chunk_result = response.chunk_result
    raw_text = parsed_text.raw_text if parsed_text is not None else ""
    ocr_message = ocr_stage.message if ocr_stage is not None else None
    ocr_failed_blocks = extract_ocr_failed_blocks(ocr_message)
    if failed_stage is not None:
        status = "failed"
    elif ocr_failed_blocks > 0:
        status = "warning"
    else:
        status = "success"

    return FileValidationResult(
        source_path=response.source_path,
        status=status,
        mode=mode,
        policy_name_guess=response.policy_name_guess,
        policy_name_resolved=target_policy_name or response.policy_name_guess,
        version_label=response.derived_version_label,
        parse_method=parsed_text.parse_method if parsed_text is not None else None,
        suspected_scanned=parsed_text.suspected_scanned if parsed_text is not None else None,
        ocr_stage_status=ocr_stage.status if ocr_stage is not None else None,
        ocr_message=ocr_message,
        ocr_failed_blocks=ocr_failed_blocks,
        text_length=len(raw_text.strip()),
        section_count=section_result.total_sections if section_result is not None else 0,
        chunk_count=chunk_result.total_chunks if chunk_result is not None else 0,
        persisted=bool(persistence.persisted) if persistence is not None else False,
        requested_target_document_id=response.target_document_id,
        document_id=persistence.document_id if persistence is not None else None,
        version_id=persistence.version_id if persistence is not None else None,
        error=failed_stage.message if failed_stage is not None else None,
        raw_text_preview=raw_text[:300],
    )


def extract_ocr_failed_blocks(ocr_message: str | None) -> int:
    if not ocr_message:
        return 0
    match = re.search(r"失败\s+(\d+)\s+个图片块", ocr_message)
    if match is None:
        return 0
    return int(match.group(1))


def resolve_target_document_id(
    *,
    target_document_id: int | None,
    target_policy_name: str | None,
    policy_category: str,
    responsible_department: str | None,
) -> int | None:
    if target_document_id is not None:
        return target_document_id
    if not target_policy_name:
        return None

    session = SessionLocal()
    try:
        document = session.scalar(
            select(PolicyDocument)
            .where(PolicyDocument.policy_name == target_policy_name)
            .where(PolicyDocument.policy_category == policy_category)
            .limit(1)
        )
        if document is None:
            document = PolicyDocument(
                policy_code=None,
                policy_name=target_policy_name,
                policy_category=policy_category,
                responsible_department=responsible_department,
                current_version_id=None,
                latest_version_id=None,
                status="draft",
            )
            session.add(document)
            session.commit()
            session.refresh(document)
            return document.id

        if responsible_department and not document.responsible_department:
            document.responsible_department = responsible_department
            session.add(document)
            session.commit()
            session.refresh(document)
        return document.id
    finally:
        session.close()


def write_report(
    *,
    output_dir: Path,
    results: list[FileValidationResult],
    responses: list[PolicyPipelineResponse],
) -> None:
    csv_path = output_dir / "summary.csv"
    json_path = output_dir / "summary.json"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_path",
                "status",
                "mode",
                "policy_name_guess",
                "policy_name_resolved",
                "version_label",
                "parse_method",
                "suspected_scanned",
                "ocr_stage_status",
                "ocr_message",
                "ocr_failed_blocks",
                "text_length",
                "section_count",
                "chunk_count",
                "persisted",
                "requested_target_document_id",
                "document_id",
                "version_id",
                "error",
                "raw_text_preview",
            ],
        )
        writer.writeheader()
        for item in results:
            writer.writerow(asdict(item))

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_files": len(results),
        "success_count": sum(item.status == "success" for item in results),
        "warning_count": sum(item.status == "warning" for item in results),
        "failed_count": sum(item.status == "failed" for item in results),
        "results": [asdict(item) for item in results],
        "responses": [response.model_dump(mode="json") for response in responses],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(results: list[FileValidationResult], *, output_dir: Path) -> None:
    print(f"输出目录：{output_dir}")
    print(
        f"文件总数={len(results)} 成功={sum(item.status == 'success' for item in results)} "
        f"告警={sum(item.status == 'warning' for item in results)} "
        f"失败={sum(item.status == 'failed' for item in results)}"
    )
    for item in results:
        print(
            f"[{item.status}] {item.source_path} | parse={item.parse_method} | "
            f"ocr={item.ocr_stage_status} | ocr_failed={item.ocr_failed_blocks} | text={item.text_length} | "
            f"sections={item.section_count} | chunks={item.chunk_count} | persisted={item.persisted}"
        )
        if item.error:
            print(f"  error: {item.error}")


def main() -> None:
    args = parse_args()
    files = load_input_files(args)
    output_dir = build_output_dir(args.output_dir)

    results: list[FileValidationResult] = []
    responses: list[PolicyPipelineResponse] = []
    chained_target_document_id = (
        resolve_target_document_id(
            target_document_id=None,
            target_policy_name=args.policy_name_override,
            policy_category=args.policy_category,
            responsible_department=args.responsible_department,
        )
        if args.chain_versions
        else None
    )

    for source_path in files:
        try:
            response = run_pipeline_for_file(
                source_path=source_path,
                mode=args.mode,
                policy_category=args.policy_category,
                responsible_department=args.responsible_department,
                target_document_id=chained_target_document_id if args.chain_versions else None,
            )
            result = extract_file_result(
                response,
                mode=args.mode,
                target_policy_name=args.policy_name_override,
            )
            responses.append(response)
            results.append(result)
            if (
                args.chain_versions
                and args.mode == "ingest"
                and chained_target_document_id is None
                and response.persistence is not None
                and response.persistence.persisted
                and response.persistence.document_id is not None
            ):
                chained_target_document_id = response.persistence.document_id
        except Exception as exc:
            results.append(
                FileValidationResult(
                    source_path=str(source_path),
                    status="failed",
                    mode=args.mode,
                    policy_name_guess=None,
                    policy_name_resolved=args.policy_name_override,
                    version_label=None,
                    parse_method=None,
                    suspected_scanned=None,
                    ocr_stage_status=None,
                    ocr_message=None,
                    ocr_failed_blocks=0,
                    text_length=0,
                    section_count=0,
                    chunk_count=0,
                    persisted=False,
                    requested_target_document_id=(
                        chained_target_document_id if args.chain_versions else None
                    ),
                    document_id=None,
                    version_id=None,
                    error=str(exc),
                    raw_text_preview="",
                )
            )
            if args.fail_fast:
                break

    write_report(output_dir=output_dir, results=results, responses=responses)
    print_summary(results, output_dir=output_dir)


if __name__ == "__main__":
    main()
