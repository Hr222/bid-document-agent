class UpstreamServiceError(RuntimeError):
    """外部模型或服务提供方请求失败时抛出的异常。"""


class ServiceNotConfiguredError(RuntimeError):
    """功能依赖的服务端配置缺失时抛出的异常。"""
