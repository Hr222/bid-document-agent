from typing import Any

from pydantic import BaseModel, Field


class PersistenceResult(BaseModel):
    persisted: bool
    document_id: int | None = None
    version_id: int | None = None
    version_seq: int | None = None
    version_label: str | None = None
    section_count: int = 0
    chunk_count: int = 0
    message: str


class SectionSplitItem(BaseModel):
    section_no: str | None = None
    section_title: str | None = None
    section_level: int
    section_path: str | None = None
    section_order: int
    section_text: str
    page_start: int | None = None
    page_end: int | None = None
    source_block_start: int | None = None
    source_block_end: int | None = None


class SectionSplitResult(BaseModel):
    total_sections: int
    strategy: str
    sections: list[SectionSplitItem] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ChunkItem(BaseModel):
    chunk_index: int
    section_order: int
    section_title: str | None = None
    section_path: str | None = None
    section_id: int | None = None
    page_no: int | None = None
    chunk_text: str
    chunk_in_section: int
    chunk_start_offset: int
    chunk_end_offset: int
    char_count: int
    source_block_start: int | None = None
    source_block_end: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class ChunkSampleItem(BaseModel):
    section_title: str | None = None
    section_path: str | None = None
    chunk_preview: str
    char_count: int


class ChunkSplitResult(BaseModel):
    total_chunks: int
    strategy: str
    notes: list[str] = Field(default_factory=list)
    chunks: list[ChunkItem] = Field(default_factory=list)
    sample_chunks: list[ChunkSampleItem] = Field(default_factory=list)

__all__ = [
    "ChunkItem",
    "ChunkSampleItem",
    "ChunkSplitResult",
    "PersistenceResult",
    "SectionSplitItem",
    "SectionSplitResult",
]
