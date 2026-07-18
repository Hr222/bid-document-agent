from app.application import ApplicationContainer
from app.domain.policy import COURT_EVALUATION_MATERIALS_SCENARIO


def test_application_container_registers_current_scenario_provider() -> None:
    container = ApplicationContainer(session=object())

    registry = container.checklist_data_provider_registry()

    assert registry.list_registered_scenarios() == (
        COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code,
    )


def test_application_container_builds_bridge_with_shared_services() -> None:
    container = ApplicationContainer(session=object())

    bridge = container.policy_capability_bridge()

    assert bridge.retrieval_service is container.knowledge_retrieval_service()
    assert bridge.rule_retrieval_service is container.policy_rule_retrieval_service()
    assert bridge.data_acquisition_service is container.policy_data_acquisition_service()
    assert bridge.checklist_decision_service is container.checklist_decision_service()
