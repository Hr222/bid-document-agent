"""应用装配层导出。

这里作为当前阶段的组合根，统一收口 service、provider 与桥接层装配，
避免路由层和未来编排层各自重复 new 依赖。
"""

from app.application.container import ApplicationContainer

__all__ = ["ApplicationContainer"]
