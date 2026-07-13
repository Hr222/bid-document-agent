from __future__ import annotations

from app.schemas.policy_decision import PolicyDecisionChecklistRequest
from app.services.policy_decision.contracts import ChecklistSubmissionPayload


class InlineChecklistDataProvider:
    """直接从请求体中提取并去重提交材料。"""

    provider_name = "inline_submitted_materials"

    def collect(self, request: PolicyDecisionChecklistRequest) -> ChecklistSubmissionPayload:
        """清洗空白项并保留首个有效材料名称。"""
        deduplicated_materials: list[str] = []
        for item in request.submitted_materials:
            normalized = item.strip()
            if normalized and normalized not in deduplicated_materials:
                deduplicated_materials.append(normalized)
        return ChecklistSubmissionPayload(submitted_materials=deduplicated_materials)
