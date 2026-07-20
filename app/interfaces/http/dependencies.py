from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.composition import ApplicationContainer
from app.infrastructure.persistence.session import SessionLocal
from app.modules.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.modules.knowledge.application.knowledge_base import KnowledgeBaseService
from app.modules.knowledge.application.publication_service import KnowledgePublicationService
from app.modules.online.application.policy_decision import PolicyDecisionApplicationService
from app.modules.online.application.rag_facade import RagApplicationFacade


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


def get_rag_application_facade(
    container: ApplicationContainer = Depends(get_application_container),
) -> RagApplicationFacade:
    """提供在线 RAG 应用外观层，HTTP 与 Agent 共用同一入口。"""
    return container.rag_application_facade()


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


def get_policy_pipeline_preview_service(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> PolicyPipelineService:
    """提供预览模式流水线服务。"""
    return container.policy_pipeline_preview_service()


def get_policy_pipeline_ingest_service(
    container: ApplicationContainer = Depends(get_application_container),
) -> PolicyPipelineService:
    """提供入库模式流水线服务。"""
    return container.policy_pipeline_ingest_service()


def get_policy_upload_service(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> PolicyUploadService:
    """提供上传暂存服务。"""
    return container.policy_upload_service()


def get_policy_ingestion_service(
    container: ApplicationContainer = Depends(get_stateless_application_container),
) -> PolicyIngestionService:
    """提供候选文件扫描服务。"""
    return container.policy_ingestion_service()


def get_knowledge_base_service(
    container: ApplicationContainer = Depends(get_application_container),
) -> KnowledgeBaseService:
    """提供知识库轻量管理服务。"""
    return container.knowledge_base_service()
