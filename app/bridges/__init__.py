"""桥接层导出。

这里统一暴露面向后续编排框架的稳定能力接口，
让 LangChain / LangGraph 只依赖桥接层，而不直接依赖当前阶段内部 service 细节。
"""

from app.bridges.policy_capability_bridge import PolicyCapabilityBridge

__all__ = ["PolicyCapabilityBridge"]
