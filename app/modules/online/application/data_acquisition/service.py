from __future__ import annotations

from app.modules.online.application.data_acquisition.contracts import (
    ChecklistDataAcquisitionRequest,
)
from app.modules.online.application.data_acquisition.models import ChecklistDataPack
from app.modules.online.application.data_acquisition.providers import InlineChecklistDataProvider
from app.modules.online.application.data_acquisition.registry import ChecklistDataProviderRegistry
from app.modules.online.domain.policy import COURT_EVALUATION_MATERIALS_SCENARIO


class PolicyDataAcquisitionService:
    """面向业务场景消费数据提供者，并输出统一数据包。"""

    def __init__(
        self,
        provider_registry: ChecklistDataProviderRegistry | None = None,
    ) -> None:
        if provider_registry is None:
            provider_registry = ChecklistDataProviderRegistry()
            provider_registry.register(
                COURT_EVALUATION_MATERIALS_SCENARIO.scenario_code,
                InlineChecklistDataProvider(),
            )
        self.provider_registry = provider_registry

    def acquire_checklist_data(self, request: ChecklistDataAcquisitionRequest) -> ChecklistDataPack:
        """按场景收集本次核验所需的最小业务数据。"""
        provider = self.provider_registry.get(request.scenario_code)
        return provider.collect(request)
