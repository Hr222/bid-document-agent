from __future__ import annotations

from app.scripts.run_retrieval_baseline import (
    BenchmarkCaseResult,
    StrategyCaseResult,
    build_comparison_summary,
    build_strategy_summary,
)
from app.services.retrieval.vector_search import VectorSearchStrategyName


def make_strategy_case_result(
    *,
    strategy: VectorSearchStrategyName,
    elapsed_ms: float,
    hit_count: int,
    top1_document_match: bool,
    top1_section_match: bool,
    top3_section_match: bool,
) -> StrategyCaseResult:
    """构造最小策略结果，便于聚焦 benchmark 汇总逻辑。"""

    return StrategyCaseResult(
        strategy=strategy,
        pipeline_strategy=f"hybrid-vector-keyword/{strategy}",
        vector_trace_source=f"source-{strategy}",
        elapsed_ms=elapsed_ms,
        hit_count=hit_count,
        top1_document_match=top1_document_match,
        top1_section_match=top1_section_match,
        top3_section_match=top3_section_match,
        top_hits=[],
    )


def test_build_strategy_summary_aggregates_counts_and_latency() -> None:
    results = [
        BenchmarkCaseResult(
            case_id="case-1",
            query="问题一",
            expected_document_name="制度A",
            expected_section_title="第一条",
            strategy_results={
                "exact": make_strategy_case_result(
                    strategy="exact",
                    elapsed_ms=12.0,
                    hit_count=3,
                    top1_document_match=True,
                    top1_section_match=True,
                    top3_section_match=True,
                ),
                "hnsw": make_strategy_case_result(
                    strategy="hnsw",
                    elapsed_ms=8.0,
                    hit_count=3,
                    top1_document_match=True,
                    top1_section_match=True,
                    top3_section_match=True,
                ),
            },
        ),
        BenchmarkCaseResult(
            case_id="case-2",
            query="问题二",
            expected_document_name="制度B",
            expected_section_title="第二条",
            strategy_results={
                "exact": make_strategy_case_result(
                    strategy="exact",
                    elapsed_ms=18.0,
                    hit_count=0,
                    top1_document_match=False,
                    top1_section_match=False,
                    top3_section_match=False,
                ),
                "hnsw": make_strategy_case_result(
                    strategy="hnsw",
                    elapsed_ms=14.0,
                    hit_count=1,
                    top1_document_match=False,
                    top1_section_match=False,
                    top3_section_match=False,
                ),
            },
        ),
    ]

    summary = build_strategy_summary(results, "exact")

    assert summary == {
        "total_cases": 2,
        "top1_document_match_count": 1,
        "top1_section_match_count": 1,
        "top3_section_match_count": 1,
        "zero_hit_count": 1,
        "average_hit_count": 1.5,
        "average_elapsed_ms": 15.0,
    }


def test_build_comparison_summary_marks_regression_and_speedup() -> None:
    results = [
        BenchmarkCaseResult(
            case_id="case-1",
            query="问题一",
            expected_document_name="制度A",
            expected_section_title="第一条",
            strategy_results={
                "exact": make_strategy_case_result(
                    strategy="exact",
                    elapsed_ms=12.0,
                    hit_count=3,
                    top1_document_match=True,
                    top1_section_match=True,
                    top3_section_match=True,
                ),
                "hnsw": make_strategy_case_result(
                    strategy="hnsw",
                    elapsed_ms=9.0,
                    hit_count=3,
                    top1_document_match=True,
                    top1_section_match=False,
                    top3_section_match=False,
                ),
            },
        ),
        BenchmarkCaseResult(
            case_id="case-2",
            query="问题二",
            expected_document_name="制度B",
            expected_section_title="第二条",
            strategy_results={
                "exact": make_strategy_case_result(
                    strategy="exact",
                    elapsed_ms=15.0,
                    hit_count=2,
                    top1_document_match=False,
                    top1_section_match=False,
                    top3_section_match=False,
                ),
                "hnsw": make_strategy_case_result(
                    strategy="hnsw",
                    elapsed_ms=18.0,
                    hit_count=3,
                    top1_document_match=True,
                    top1_section_match=True,
                    top3_section_match=True,
                ),
            },
        ),
    ]

    comparison = build_comparison_summary(results)

    assert comparison == {
        "compared_case_count": 2,
        "candidate_top1_document_better_count": 1,
        "candidate_top1_document_worse_count": 0,
        "candidate_top1_section_better_count": 1,
        "candidate_top1_section_worse_count": 1,
        "candidate_top3_section_better_count": 1,
        "candidate_top3_section_worse_count": 1,
        "candidate_faster_case_count": 1,
        "baseline_faster_case_count": 1,
        "same_latency_case_count": 0,
        "average_elapsed_delta_ms": 0.0,
        "top3_section_regression_case_ids": ["case-1"],
    }
