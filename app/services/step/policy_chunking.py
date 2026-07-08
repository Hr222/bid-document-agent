"""兼容旧导入路径的切块步骤包装层。"""

from app.services.ingestion.steps.policy_chunking import PolicyChunkingService

__all__ = ["PolicyChunkingService"]
