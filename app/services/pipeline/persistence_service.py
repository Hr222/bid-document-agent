"""兼容旧导入路径的入库持久化服务包装层。"""

from app.services.ingestion.persistence import PolicyPersistenceService

__all__ = ["PolicyPersistenceService"]
