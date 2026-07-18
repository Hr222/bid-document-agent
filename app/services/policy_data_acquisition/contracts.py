from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.policy_decision import PolicyDecisionChecklistRequest
from app.services.policy_data_acquisition.models import ChecklistDataPack


@dataclass(slots=True, frozen=True)
class ChecklistDataAcquisitionRequest:
    """统一承载数据获取阶段所需的场景与请求上下文。"""

    scenario_code: str
    checklist_request: PolicyDecisionChecklistRequest


class ChecklistDataProvider(Protocol):
    """抽象业务数据来源，允许后续接入表单、数据库或外部系统。"""

    provider_name: str

    def collect(self, request: ChecklistDataAcquisitionRequest) -> ChecklistDataPack: ...
