from __future__ import annotations

import logging
from logging.config import dictConfig

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """为应用和 Uvicorn 日志器配置控制台日志。"""
    global _CONFIGURED
    if _CONFIGURED:
        return

    normalized_level = level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                }
            },
            "root": {
                "level": normalized_level,
                "handlers": ["console"],
            },
            "loggers": {
                "app": {
                    "level": normalized_level,
                    "propagate": True,
                },
                "uvicorn.error": {
                    "level": normalized_level,
                },
                "uvicorn.access": {
                    "level": normalized_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
