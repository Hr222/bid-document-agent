from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgePublicationRequest(BaseModel):
    document_id: int = Field(..., ge=1)
    version_id: int = Field(..., ge=1)


class KnowledgePublicationResponse(BaseModel):
    document_id: int
    version_id: int
    version_status: str
