from __future__ import annotations

from typing import Protocol


class KnowledgeWritePort(Protocol):
    """入库用例依赖的知识写入端口。

    具体参数仍由入库流水线的内部上下文提供，端口不依赖 HTTP Schema。
    """

    def save_document_version_blocks_sections_and_chunks(self, **kwargs: object) -> object: ...
