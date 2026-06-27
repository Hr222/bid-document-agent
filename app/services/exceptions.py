class UpstreamServiceError(RuntimeError):
    """Raised when an external model provider request fails."""


class ServiceNotConfiguredError(RuntimeError):
    """Raised when a feature depends on missing server-side configuration."""
