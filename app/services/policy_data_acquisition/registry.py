from __future__ import annotations

from app.services.policy_data_acquisition.contracts import ChecklistDataProvider
from app.services.policy_data_acquisition.providers import InlineChecklistDataProvider


class ChecklistDataProviderRegistry:
    """统一维护场景到数据 Provider 的映射关系。"""

    def __init__(
        self,
        *,
        default_provider: ChecklistDataProvider | None = None,
    ) -> None:
        self._providers: dict[str, ChecklistDataProvider] = {}
        self._default_provider = default_provider or InlineChecklistDataProvider()

    def register(self, scenario_code: str, provider: ChecklistDataProvider) -> None:
        """注册某个场景专用的数据 Provider，便于后续接入真实外部系统。"""
        normalized_code = scenario_code.strip()
        if not normalized_code:
            raise ValueError("scenario_code 不能为空。")
        self._providers[normalized_code] = provider

    def get(self, scenario_code: str) -> ChecklistDataProvider:
        """按场景编码获取 Provider；未单独注册时回落到默认 Provider。"""
        normalized_code = scenario_code.strip()
        if not normalized_code:
            raise ValueError("scenario_code 不能为空。")
        return self._providers.get(normalized_code, self._default_provider)

    def list_registered_scenarios(self) -> tuple[str, ...]:
        """列出当前已显式注册 Provider 的场景编码。"""
        return tuple(self._providers.keys())
