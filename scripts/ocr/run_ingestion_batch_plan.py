from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from scripts.ocr.batch_ingestion_validation import (
    FileValidationResult,
    build_output_dir,
    extract_file_result,
    resolve_target_document_id,
    run_pipeline_for_file,
)


@dataclass(slots=True)
class BatchPlanGroup:
    group_name: str
    policy_name: str
    policy_category: str
    files: list[str]
    chain_versions: bool = False
    reverse_input: bool = False
    responsible_department: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按批次计划执行制度样本批量入库。")
    parser.add_argument("--plan", required=True, help="批次计划 JSON 文件路径。")
    parser.add_argument(
        "--mode",
        choices=("preview", "ingest"),
        default="ingest",
        help="执行模式：preview 只跑流程，ingest 正式入库。",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="可选输出目录，默认写入 scripts/ocr/output/<时间戳>/",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="正式入库前清空 kb_policy_* 测试数据。",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="任一文件失败后立即停止。",
    )
    return parser.parse_args()


def load_plan(plan_path: str) -> tuple[str, list[BatchPlanGroup]]:
    payload = json.loads(Path(plan_path).expanduser().resolve().read_text(encoding="utf-8"))
    batch_name = str(payload.get("batch_name") or Path(plan_path).stem)
    groups: list[BatchPlanGroup] = []
    for raw_group in payload.get("groups", []):
        groups.append(
            BatchPlanGroup(
                group_name=raw_group["group_name"],
                policy_name=raw_group["policy_name"],
                policy_category=raw_group["policy_category"],
                files=list(raw_group["files"]),
                chain_versions=bool(raw_group.get("chain_versions", False)),
                reverse_input=bool(raw_group.get("reverse_input", False)),
                responsible_department=raw_group.get("responsible_department"),
            )
        )
    if not groups:
        raise ValueError("批次计划中没有任何 group。")
    return batch_name, groups


def clear_kb_tables() -> None:
    session = SessionLocal()
    try:
        session.execute(
            text(
                "TRUNCATE TABLE "
                "kb_policy_chunk, kb_policy_section, kb_policy_block, "
                "kb_policy_version, kb_policy_document "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
    finally:
        session.close()


def normalize_group_files(group: BatchPlanGroup) -> list[Path]:
    resolved = [Path(item).expanduser().resolve() for item in group.files]
    for path in resolved:
        if not path.exists():
            raise FileNotFoundError(f"group={group.group_name} 文件不存在：{path}")
        if not path.is_file():
            raise IsADirectoryError(f"group={group.group_name} 路径不是文件：{path}")
    if group.reverse_input:
        resolved.reverse()
    return resolved


def run_group(
    *,
    group: BatchPlanGroup,
    mode: str,
    fail_fast: bool,
) -> tuple[list[dict[str, object]], list[FileValidationResult], list[object]]:
    files = normalize_group_files(group)
    results: list[FileValidationResult] = []
    responses: list[object] = []
    rows: list[dict[str, object]] = []

    should_bind_target_document = group.chain_versions or len(files) == 1
    resolved_group_policy_name = group.policy_name if should_bind_target_document else None
    target_document_id = (
        resolve_target_document_id(
            target_document_id=None,
            target_policy_name=group.policy_name,
            policy_category=group.policy_category,
            responsible_department=group.responsible_department,
        )
        if mode == "ingest" and should_bind_target_document
        else None
    )

    for source_path in files:
        try:
            response = run_pipeline_for_file(
                source_path=source_path,
                mode=mode,
                policy_category=group.policy_category,
                responsible_department=group.responsible_department,
                target_document_id=target_document_id if should_bind_target_document else None,
            )
            result = extract_file_result(
                response,
                mode=mode,
                target_policy_name=resolved_group_policy_name,
            )
            responses.append(response)
            results.append(result)
            rows.append(
                {
                    "group_name": group.group_name,
                    "policy_name": group.policy_name,
                    "policy_category": group.policy_category,
                    "chain_versions": group.chain_versions,
                    **asdict(result),
                }
            )
        except Exception as exc:
            result = FileValidationResult(
                source_path=str(source_path),
                status="failed",
                mode=mode,
                policy_name_guess=None,
                policy_name_resolved=resolved_group_policy_name,
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
                requested_target_document_id=target_document_id if should_bind_target_document else None,
                document_id=None,
                version_id=None,
                error=str(exc),
                raw_text_preview="",
            )
            results.append(result)
            rows.append(
                {
                    "group_name": group.group_name,
                    "policy_name": group.policy_name,
                    "policy_category": group.policy_category,
                    "chain_versions": group.chain_versions,
                    **asdict(result),
                }
            )
            if fail_fast:
                break

    return rows, results, responses


def write_plan_summary(
    *,
    output_dir: Path,
    batch_name: str,
    rows: list[dict[str, object]],
) -> None:
    csv_path = output_dir / "batch_summary.csv"
    json_path = output_dir / "batch_summary.json"

    fieldnames = [
        "group_name",
        "policy_name",
        "policy_category",
        "chain_versions",
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
    ]

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    payload = {
        "batch_name": batch_name,
        "generated_at": datetime.now(UTC).isoformat(),
        "total_files": len(rows),
        "success_count": sum(row["status"] == "success" for row in rows),
        "warning_count": sum(row["status"] == "warning" for row in rows),
        "failed_count": sum(row["status"] == "failed" for row in rows),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_group_summary(group: BatchPlanGroup, results: list[FileValidationResult]) -> None:
    print(
        f"group={group.group_name} "
        f"files={len(results)} "
        f"success={sum(item.status == 'success' for item in results)} "
        f"warning={sum(item.status == 'warning' for item in results)} "
        f"failed={sum(item.status == 'failed' for item in results)}"
    )
    for item in results:
        print(
            f"  [{item.status}] {item.source_path} | "
            f"doc={item.policy_name_resolved} | "
            f"parse={item.parse_method} | sections={item.section_count} | "
            f"chunks={item.chunk_count} | persisted={item.persisted}"
        )
        if item.error:
            print(f"    error: {item.error}")


def main() -> None:
    args = parse_args()
    batch_name, groups = load_plan(args.plan)
    output_dir = build_output_dir(args.output_dir)

    if args.clear_db:
        if args.mode != "ingest":
            raise ValueError("--clear-db 只能和 --mode ingest 一起使用。")
        clear_kb_tables()

    all_rows: list[dict[str, object]] = []
    total_results: list[FileValidationResult] = []

    for group in groups:
        rows, results, _ = run_group(
            group=group,
            mode=args.mode,
            fail_fast=args.fail_fast,
        )
        all_rows.extend(rows)
        total_results.extend(results)
        print_group_summary(group, results)
        if args.fail_fast and any(item.status == "failed" for item in results):
            break

    write_plan_summary(output_dir=output_dir, batch_name=batch_name, rows=all_rows)
    print(
        f"batch={batch_name} output={output_dir} total={len(total_results)} "
        f"success={sum(item.status == 'success' for item in total_results)} "
        f"warning={sum(item.status == 'warning' for item in total_results)} "
        f"failed={sum(item.status == 'failed' for item in total_results)}"
    )


if __name__ == "__main__":
    main()
