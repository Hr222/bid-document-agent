from app.composition import ApplicationContainer
from app.modules.online.domain.policy import COURT_EVALUATION_MATERIALS_SCENARIO


def test_application_container_registers_current_scenario_provider() -> None:
    container = ApplicationContainer(session=object())

    registry = container.checklist_data_provider_registry()

    assert registry.list_registered_scenarios() == (
        COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code,
    )


def test_application_container_builds_online_services_with_shared_dependencies() -> None:
    container = ApplicationContainer(session=object())

    query_capability = container.knowledge_query_capability()
    decision_service = container.policy_decision_application_service()

    assert query_capability.read_port is container.knowledge_read_repository()
    assert decision_service.engine is container.checklist_decision_service()
