from __future__ import annotations

from app.schemas.policy_decision import PolicyDecisionChecklistRequest
from app.services.policy_data_acquisition import (
    ChecklistDataAcquisitionRequest,
    ChecklistDataProviderRegistry,
    InlineChecklistDataProvider,
    PolicyDataAcquisitionService,
)


def test_data_acquisition_service_deduplicates_inline_materials_and_builds_trace() -> None:
    service = PolicyDataAcquisitionService()

    data_pack = service.acquire_checklist_data(
        ChecklistDataAcquisitionRequest(
            scenario_code="court-evaluation-materials-review",
            checklist_request=PolicyDecisionChecklistRequest(
                submitted_materials=["申请书", " 申请书 ", "机构简介", " "]
            ),
        )
    )

    assert data_pack.is_sufficient is True
    assert list(data_pack.submitted_materials) == ["申请书", "机构简介"]
    assert list(data_pack.provided_input_fields) == ["已提交材料列表"]
    assert list(data_pack.missing_input_fields) == []
    assert data_pack.field_traces[0].value_count == 2


def test_data_acquisition_service_marks_missing_input_when_materials_not_provided() -> None:
    service = PolicyDataAcquisitionService()

    data_pack = service.acquire_checklist_data(
        ChecklistDataAcquisitionRequest(
            scenario_code="court-evaluation-materials-review",
            checklist_request=PolicyDecisionChecklistRequest(),
        )
    )

    assert data_pack.is_sufficient is False
    assert list(data_pack.submitted_materials) == []
    assert list(data_pack.missing_input_fields) == ["已提交材料列表"]
    assert data_pack.insufficient_reason is not None


def test_data_provider_registry_supports_scenario_specific_registration() -> None:
    registry = ChecklistDataProviderRegistry()
    provider = InlineChecklistDataProvider()
    registry.register("court-evaluation-materials-review", provider)

    service = PolicyDataAcquisitionService(registry)
    data_pack = service.acquire_checklist_data(
        ChecklistDataAcquisitionRequest(
            scenario_code="court-evaluation-materials-review",
            checklist_request=PolicyDecisionChecklistRequest(submitted_materials=["申请书"]),
        )
    )

    assert registry.list_registered_scenarios() == ("court-evaluation-materials-review",)
    assert data_pack.provider_name == provider.provider_name
