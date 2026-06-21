from pydantic import BaseModel, Field

from app.schemas.policy_pipeline import PolicyPipelineResponse


class PolicyUploadIngestRequest(BaseModel):
    upload_id: str = Field(..., min_length=1)
    policy_category: str = Field(default="管理制度", min_length=1)
    responsible_department: str | None = None
    version_label: str | None = None


class PolicyUploadPreviewResponse(PolicyPipelineResponse):
    upload_id: str
