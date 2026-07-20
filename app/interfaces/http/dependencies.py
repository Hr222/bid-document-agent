from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.composition import ApplicationContainer
from app.infrastructure.filesystem.upload_service import PolicyUploadService
from app.infrastructure.persistence.session import SessionLocal
from app.modules.ingestion.application.ingestion_use_case import IngestionUseCase
from app.modules.ingestion.application.scan_candidates import PolicyCandidateScanUseCase
from app.modules.knowledge.application.knowledge_base import KnowledgeBaseService
from app.modules.knowledge.application.publication_service import KnowledgePublicationService
from app.modules.online.application.ask_knowledge import AskKnowledgeUseCase
from app.modules.online.application.policy_decision import PolicyDecisionApplicationService


def get_db_session() -> Generator[Session, None, None]:
    """为每个请求提供一个数据库会话，并在结束后关闭。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_application_container(
    session: Session = Depends(get_db_session),
) -> ApplicationContainer:
    """为需要数据库能力的请求提供统一装配容器。"""
    return ApplicationContainer(session)


def get_stateless_application_container() -> ApplicationContainer:
    """为纯内存或文件系统能力提供无会话容器。"""
    return ApplicationContainer()


def get_ask_knowledge_use_case(
    container: ApplicationContainer = Depends(get_application_container),
) -> AskKnowledgeUseCase:
    """提供在线知识问答应用用例。"""
    return container.ask_knowledge_use_case()


def get_policy_decision_application_service(
    container: ApplicationContainer = Depends(get_application_container),
) -> PolicyDecisionApplicationService:
    """提供规则决策应用用例。"""
    return container.policy_decision_application_service()


def get_knowledge_publication_service(
    container: ApplicationContainer = Depends(get_application_container),
) -> KnowledgePublicationService:
    """提供知识版本发布用例。"""
    return container.knowledge_publication_service()


def get_ingestion_preview_use_case(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> IngestionUseCase:
    """提供文档入库预览用例。"""
    return container.ingestion_preview_use_case()


def get_ingestion_use_case(
    container: ApplicationContainer = Depends(get_application_container),
) -> IngestionUseCase:
    """提供文档入库用例。"""
    return container.ingestion_use_case()


def get_policy_upload_service(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> PolicyUploadService:
    """提供上传暂存服务。"""
    return container.policy_upload_service()


def get_policy_candidate_scan_use_case(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> PolicyCandidateScanUseCase:
    """提供候选文件扫描用例。"""
    return container.policy_candidate_scan_use_case()


def get_knowledge_base_service(
    container: ApplicationContainer = Depends(get_application_container),
) -> KnowledgeBaseService:
    """提供知识库轻量管理服务。"""
    return container.knowledge_base_service()
