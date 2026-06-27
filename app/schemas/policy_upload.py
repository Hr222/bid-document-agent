from pydantic import BaseModel, Field

from app.schemas import PolicyPipelineResponse


class PolicyUploadIngestRequest(BaseModel):
    """上传文件后的正式入库请求。"""

    upload_id: str = Field(..., min_length=1, description="上传暂存 ID。")
    policy_category: str = Field(default="管理制度", min_length=1, description="资料分类。")
    responsible_department: str | None = Field(default=None, description="责任部门。")
    version_label: str | None = Field(default=None, description="手工指定的版本标签。")


class PolicyUploadPreviewResponse(PolicyPipelineResponse):
    """上传预览响应。"""

    upload_id: str = Field(description="上传暂存 ID。")
