"""兼容旧导入路径的入库 pipeline 包装包。"""

from app.services.ingestion.pipeline import PolicyPipelineService

__all__ = ["PolicyPipelineService"]
