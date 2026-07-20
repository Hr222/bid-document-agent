from __future__ import annotations

from typing import Protocol


class KnowledgePublicationPort(Protocol):
    """知识版本发布/激活端口。"""

    def activate_version(self, *, document_id: int, version_id: int) -> object: ...
