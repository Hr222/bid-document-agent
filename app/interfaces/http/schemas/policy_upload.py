from pydantic import BaseModel, Field

from app.interfaces.http.schemas import PolicyPipelineResponse


class PolicyUploadIngestRequest(BaseModel):
    """上传文件后的正式入库请求。"""

    upload_id: str = Field(
        ...,
        min_length=32,
        max_length=32,
        pattern=r"^[0-9a-fA-F]{32}$",
        description="上传暂存 ID。",
    )
    policy_category: str = Field(default="管理制度", min_length=1, description="资料分类。")
    responsible_department: str | None = Field(default=None, description="责任部门。")
    version_label: str | None = Field(default=None, description="手工指定的版本标签。")
    target_document_id: int | None = Field(
        default=None,
        ge=1,
        description="显式指定要挂接的已有制度主档 ID。",
    )


class PolicyUploadPreviewResponse(PolicyPipelineResponse):
    """上传预览响应。"""

    upload_id: str = Field(description="上传暂存 ID。")
