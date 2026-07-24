from fastapi.testclient import TestClient

from app.interfaces.http.dependencies import get_knowledge_management_service
from app.main import create_app
from app.modules.knowledge.application.management_contracts import (
    KnowledgeManagementDocument,
    KnowledgeManagementDocumentPage,
    KnowledgeManagementOverviewResult,
    ListKnowledgeManagementDocumentsQuery,
)
from app.modules.knowledge.application.management_service import KnowledgeManagementService


class FakeManagementReadPort:
    def __init__(self) -> None:
        self.queries: list[ListKnowledgeManagementDocumentsQuery] = []

    def get_overview(self) -> KnowledgeManagementOverviewResult:
        return KnowledgeManagementOverviewResult(
            document_count=0,
            chunk_count=0,
            pending_count=0,
            failed_count=0,
            latest_updated_at=None,
        )

    def list_management_categories(self) -> list[str]:
        return ["管理制度"]

    def list_management_documents(
        self,
        query: ListKnowledgeManagementDocumentsQuery,
    ) -> KnowledgeManagementDocumentPage:
        self.queries.append(query)
        return KnowledgeManagementDocumentPage(items=[self._document()], total_count=1)

    def get_document(self, document_id: int) -> KnowledgeManagementDocument | None:
        return self._document() if document_id == 1 else None

    @staticmethod
    def _document() -> KnowledgeManagementDocument:
        return KnowledgeManagementDocument(
            document_id=1,
            policy_name="资产评估师登记卡",
            policy_category="管理制度",
            responsible_department=None,
            file_name="资产评估师登记卡.pdf",
            file_type="pdf",
            file_size_bytes=None,
            version_id=1,
            version_label="v1.0",
            processing_status="ready",
            processing_progress=100,
            publication_status="active",
            parser_status="parsed",
            section_count=1,
            chunk_count=1,
            updated_at=None,
            updated_by=None,
            error_message=None,
        )


def test_management_document_query_supports_empty_and_repeated_status_parameters() -> None:
    port = FakeManagementReadPort()
    application = create_app()
    application.dependency_overrides[get_knowledge_management_service] = lambda: (
        KnowledgeManagementService(port)
    )

    client = TestClient(application)
    assert client.get("/api/v1/kb/management/documents").status_code == 200
    response = client.get(
        "/api/v1/kb/management/documents",
        params=[
            ("document_name", "资产"),
            ("status", "ready"),
            ("status", "failed"),
            ("policy_category", "管理制度"),
        ],
    )

    assert response.status_code == 200
    assert port.queries[-1].document_name == "资产"
    assert port.queries[-1].statuses == ("ready", "failed")
    assert port.queries[-1].policy_category == "管理制度"

    application.dependency_overrides.clear()
