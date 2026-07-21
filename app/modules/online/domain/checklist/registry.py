from __future__ import annotations

from dataclasses import dataclass

from app.modules.online.domain.checklist.definitions import (
    COURT_EVALUATION_MATERIALS_SCENARIO,
    ChecklistScenarioDefinition,
)


class ScenarioNotFoundError(ValueError):
    """当调用方请求不存在的场景时，返回统一错误。"""


@dataclass(slots=True)
class ChecklistScenarioRegistry:
    """统一维护当前系统已注册的 checklist 场景定义。"""

    _definitions: dict[str, ChecklistScenarioDefinition]

    def __init__(self, definitions: tuple[ChecklistScenarioDefinition, ...] = ()) -> None:
        self._definitions = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: ChecklistScenarioDefinition) -> None:
        """注册单个场景定义，避免后续继续散落 import 常量。"""
        self._definitions[definition.scenario_code] = definition

    def get(self, scenario_code: str) -> ChecklistScenarioDefinition:
        """按场景编码获取定义，不存在时抛出统一异常。"""
        definition = self._definitions.get(scenario_code)
        if definition is None:
            raise ScenarioNotFoundError(f"未注册的 checklist 场景：{scenario_code}")
        return definition

    def default(self) -> ChecklistScenarioDefinition:
        """返回未指定场景时使用的默认场景定义。"""
        try:
            return next(iter(self._definitions.values()))
        except StopIteration as exc:
            raise ScenarioNotFoundError("当前未注册有效的 checklist 场景。") from exc

    def list_all(self) -> tuple[ChecklistScenarioDefinition, ...]:
        """列出当前已接入的全部 checklist 场景。"""
        return tuple(self._definitions.values())


CHECKLIST_SCENARIO_REGISTRY = ChecklistScenarioRegistry(
    definitions=(COURT_EVALUATION_MATERIALS_SCENARIO,),
)
