from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str = Field(description="服务状态。")
    app_name: str = Field(description="应用名称。")
    app_version: str = Field(description="应用版本。")
    timestamp: datetime = Field(description="响应时间。")
