from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application import ApplicationContainer
from app.bridges import PolicyCapabilityBridge
from app.db.session import SessionLocal
from app.services.ingestion import (
    PolicyIngestionService,
    PolicyPipelineService,
    PolicyUploadService,
)
from app.services.knowledge_base import KnowledgeBaseService


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


def get_policy_capability_bridge(
    container: ApplicationContainer = Depends(get_application_container),
) -> PolicyCapabilityBridge:
    """提供当前阶段统一对外能力桥接层。"""
    return container.policy_capability_bridge()


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
