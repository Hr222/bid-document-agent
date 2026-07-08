"""兼容旧导入路径的入库扫描服务包装层。"""

from app.services.ingestion.scan_service import PolicyIngestionService

__all__ = ["PolicyIngestionService"]
