from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    timestamp: datetime
