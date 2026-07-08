from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.db.session import SessionLocal
from app.repositories.policy_repository import PolicyRepository
from app.schemas import RetrievalSearchRequest
from app.services.retrieval import KnowledgeRetrievalService


@dataclass(slots=True)
class BaselineHitSummary:
    """记录单条命中结果的最小摘要，便于后续人工复核。"""

    rank: int
    policy_name: str
    section_title: str | None
    section_path: str | None
    score: float
    chunk_text_preview: str


@dataclass(slots=True)
class BaselineCaseResult:
    """记录单个评测问题的 baseline 结果。"""

    case_id: str
    query: str
    expected_document_name: str
    expected_section_title: str
    hit_count: int
    top1_document_match: bool
    top1_section_match: bool
    top3_section_match: bool
    top_hits: list[BaselineHitSummary]


def load_eval_cases(eval_path: Path) -> list[dict]:
    """读取最小评测集定义。"""

    return json.loads(eval_path.read_text(encoding="utf-8"))


def run_baseline(eval_cases: list[dict]) -> list[BaselineCaseResult]:
    """基于当前检索链路执行 baseline。"""

    session = SessionLocal()
    try:
        service = KnowledgeRetrievalService(PolicyRepository(session))
        results: list[BaselineCaseResult] = []
        for case in eval_cases:
            response = service.search(
                RetrievalSearchRequest(
                    query=case["query"],
                    top_k=5,
                )
            )
            top_hits = [
                BaselineHitSummary(
                    rank=hit.rank,
                    policy_name=hit.policy_name,
                    section_title=hit.section_title,
                    section_path=hit.section_path,
                    score=hit.score,
                    chunk_text_preview=hit.chunk_text[:120],
                )
                for hit in response.hits[:3]
            ]
            top1 = response.hits[0] if response.hits else None
            top3 = response.hits[:3]
            results.append(
                BaselineCaseResult(
                    case_id=case["case_id"],
                    query=case["query"],
                    expected_document_name=case["expected_document_name"],
                    expected_section_title=case["expected_section_title"],
                    hit_count=len(response.hits),
                    top1_document_match=(
                        top1 is not None and top1.policy_name == case["expected_document_name"]
                    ),
                    top1_section_match=(
                        top1 is not None and top1.section_title == case["expected_section_title"]
                    ),
                    top3_section_match=any(
                        hit.section_title == case["expected_section_title"] for hit in top3
                    ),
                    top_hits=top_hits,
                )
            )
        return results
    finally:
        session.close()


def build_summary(results: list[BaselineCaseResult]) -> dict:
    """汇总 baseline 指标，便于文档直接引用。"""

    total = len(results)
    return {
        "total_cases": total,
        "top1_document_match_count": sum(item.top1_document_match for item in results),
        "top1_section_match_count": sum(item.top1_section_match for item in results),
        "top3_section_match_count": sum(item.top3_section_match for item in results),
        "zero_hit_count": sum(item.hit_count == 0 for item in results),
    }


def main() -> None:
    """执行 Step A 的最小检索 baseline，并输出 JSON 结果。"""

    project_root = Path(__file__).resolve().parents[2]
    # 评测集属于测试资产，放在 tests 目录下，避免和普通说明文档混在一起。
    eval_path = project_root / "tests" / "retrieval_eval_set_step_a.json"
    eval_cases = load_eval_cases(eval_path)
    results = run_baseline(eval_cases)
    output = {
        "eval_set_file": str(eval_path.relative_to(project_root)).replace("\\", "/"),
        "summary": build_summary(results),
        "cases": [
            {
                **asdict(item),
                "top_hits": [asdict(hit) for hit in item.top_hits],
            }
            for item in results
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
