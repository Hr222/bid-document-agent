from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.composition.knowledge import build_runtime_quality_audit_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="只读盘点知识库资料、版本、解析状态和质量问题。"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="可选：将 JSON 审计报告按 UTF-8 写入指定路径。",
    )
    return parser.parse_args()


def build_output(report) -> dict:  # noqa: ANN001
    payload = asdict(report)
    payload["issue_count"] = report.issue_count
    payload["issue_counts"] = report.issue_counts
    payload["issues"] = [asdict(issue) for issue in report.issues]
    return payload


def main() -> None:
    args = parse_args()
    session, service = build_runtime_quality_audit_service()
    try:
        output_text = json.dumps(build_output(service.audit()), ensure_ascii=False, indent=2)
    finally:
        session.close()

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
    print(output_text)


if __name__ == "__main__":
    main()
