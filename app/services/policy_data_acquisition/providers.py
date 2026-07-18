from __future__ import annotations

from app.services.policy_data_acquisition.contracts import ChecklistDataAcquisitionRequest
from app.services.policy_data_acquisition.models import ChecklistDataFieldTrace, ChecklistDataPack


class InlineChecklistDataProvider:
    """直接从请求体中提取并去重提交材料，同时补齐来源 trace。"""

    provider_name = "inline_submitted_materials"
    _submitted_materials_field_key = "submitted_materials"
    _submitted_materials_label = "已提交材料列表"

    def collect(self, request: ChecklistDataAcquisitionRequest) -> ChecklistDataPack:
        """清洗空白项、去重，并显式标记输入字段是否真正提供。"""
        deduplicated_materials: list[str] = []
        for item in request.checklist_request.submitted_materials:
            normalized = item.strip()
            if normalized and normalized not in deduplicated_materials:
                deduplicated_materials.append(normalized)

        has_effective_materials = bool(deduplicated_materials)
        field_trace = ChecklistDataFieldTrace(
            field_key=self._submitted_materials_field_key,
            label=self._submitted_materials_label,
            source=self.provider_name,
            provided=has_effective_materials,
            value_count=len(deduplicated_materials),
        )
        insufficient_reason = self._build_insufficient_reason(
            request=request,
            has_effective_materials=has_effective_materials,
        )
        return ChecklistDataPack(
            scenario_code=request.scenario_code,
            provider_name=self.provider_name,
            submitted_materials=tuple(deduplicated_materials),
            field_traces=(field_trace,),
            provided_input_fields=(self._submitted_materials_label,) if has_effective_materials else (),
            missing_input_fields=(self._submitted_materials_label,) if not has_effective_materials else (),
            insufficient_reason=insufficient_reason,
        )

    def _build_insufficient_reason(
        self,
        *,
        request: ChecklistDataAcquisitionRequest,
        has_effective_materials: bool,
    ) -> str | None:
        """统一收口当前最小输入缺失时的中文原因说明。"""
        if has_effective_materials:
            return None
        if self._submitted_materials_field_key not in request.checklist_request.model_fields_set:
            return "当前请求未提供“已提交材料列表”，暂时无法进入材料核验。"
        return "当前请求虽然包含“已提交材料列表”，但其中没有有效材料名称。"
