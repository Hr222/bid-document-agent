from app.composition import ApplicationContainer
from app.modules.ingestion.application.ingestion_use_case import IngestionUseCase
from app.modules.ingestion.application.scan_candidates import PolicyCandidateScanUseCase
from app.modules.online.application.ask_knowledge import AskKnowledgeUseCase
from app.modules.online.domain.checklist import COURT_EVALUATION_MATERIALS_SCENARIO


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


def test_application_container_composes_use_cases_at_module_boundaries() -> None:
    container = ApplicationContainer(session=object())

    assert isinstance(container.ask_knowledge_use_case(), AskKnowledgeUseCase)
    assert container.ask_knowledge_use_case().facade is container.rag_application_facade()

    preview_use_case = container.ingestion_preview_use_case()
    ingest_use_case = container.ingestion_use_case()

    assert isinstance(preview_use_case, IngestionUseCase)
    assert isinstance(ingest_use_case, IngestionUseCase)
    assert isinstance(container.policy_candidate_scan_use_case(), PolicyCandidateScanUseCase)
    assert preview_use_case.pipeline.write_capability is None
    assert ingest_use_case.pipeline.write_capability is container.knowledge_write_capability()
