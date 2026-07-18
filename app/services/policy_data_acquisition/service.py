from __future__ import annotations

from app.services.policy_data_acquisition.contracts import ChecklistDataAcquisitionRequest
from app.services.policy_data_acquisition.models import ChecklistDataPack
from app.services.policy_data_acquisition.registry import ChecklistDataProviderRegistry


class PolicyDataAcquisitionService:
    """面向业务场景消费数据提供者，并输出统一数据包。"""

    def __init__(
        self,
        provider_registry: ChecklistDataProviderRegistry | None = None,
    ) -> None:
        self.provider_registry = provider_registry or ChecklistDataProviderRegistry()

    def acquire_checklist_data(self, request: ChecklistDataAcquisitionRequest) -> ChecklistDataPack:
        """按场景收集本次核验所需的最小业务数据。"""
        provider = self.provider_registry.get(request.scenario_code)
        return provider.collect(request)
