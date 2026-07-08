"""兼容旧导入路径的入库 pipeline 上下文包装层。"""

from app.services.ingestion.context import PipelineContext, PipelineMode

__all__ = ["PipelineContext", "PipelineMode"]
