from typing import Any

from pydantic import BaseModel, Field


class PersistenceResult(BaseModel):
    """落库结果。"""

    persisted: bool = Field(description="是否已成功落库。")
    document_id: int | None = Field(default=None, description="制度主表 ID。")
    version_id: int | None = Field(default=None, description="版本表 ID。")
    version_seq: int | None = Field(default=None, description="版本序号。")
    version_label: str | None = Field(default=None, description="版本标签。")
    section_count: int = Field(default=0, description="落库的章节数量。")
    chunk_count: int = Field(default=0, description="落库的切块数量。")
    message: str = Field(description="落库说明。")


class SectionSplitItem(BaseModel):
    """单个章节项。"""

    section_no: str | None = Field(default=None, description="章节编号，如第一章、第一条。")
    section_title: str | None = Field(default=None, description="章节标题。")
    section_level: int = Field(description="章节层级。")
    section_path: str | None = Field(default=None, description="章节路径。")
    section_order: int = Field(description="章节顺序号。")
    section_text: str = Field(description="章节正文。")
    page_start: int | None = Field(default=None, description="起始页码。")
    page_end: int | None = Field(default=None, description="结束页码。")
    source_block_start: int | None = Field(default=None, description="起始来源块顺序号。")
    source_block_end: int | None = Field(default=None, description="结束来源块顺序号。")


class SectionSplitResult(BaseModel):
    """章节拆分结果。"""

    total_sections: int = Field(description="章节总数。")
    strategy: str = Field(description="使用的拆分策略。")
    sections: list[SectionSplitItem] = Field(default_factory=list, description="章节列表。")
    notes: list[str] = Field(default_factory=list, description="拆分说明。")


class ChunkItem(BaseModel):
    """单个检索切块。"""

    chunk_index: int = Field(description="当前版本内的全局切块序号。")
    section_order: int = Field(description="所属章节顺序号。")
    section_title: str | None = Field(default=None, description="所属章节标题。")
    section_path: str | None = Field(default=None, description="所属章节路径。")
    section_id: int | None = Field(default=None, description="所属章节 ID。")
    page_no: int | None = Field(default=None, description="页码。")
    chunk_text: str = Field(description="切块正文。")
    chunk_in_section: int = Field(description="在当前章节内的切块序号。")
    chunk_start_offset: int = Field(description="在章节文本内的起始偏移。")
    chunk_end_offset: int = Field(description="在章节文本内的结束偏移。")
    char_count: int = Field(description="字符数。")
    source_block_start: int | None = Field(default=None, description="起始来源块序号。")
    source_block_end: int | None = Field(default=None, description="结束来源块序号。")
    metadata: dict[str, Any] = Field(default_factory=dict, description="检索元数据。")
    embedding: list[float] | None = Field(default=None, description="文本向量。")


class ChunkSampleItem(BaseModel):
    """切块摘要样例。"""

    section_title: str | None = Field(default=None, description="所属章节标题。")
    section_path: str | None = Field(default=None, description="所属章节路径。")
    chunk_preview: str = Field(description="切块摘要预览。")
    char_count: int = Field(description="字符数。")


class ChunkSplitResult(BaseModel):
    """切块结果。"""

    total_chunks: int = Field(description="切块总数。")
    strategy: str = Field(description="使用的切块策略。")
    notes: list[str] = Field(default_factory=list, description="切块说明。")
    chunks: list[ChunkItem] = Field(default_factory=list, description="完整切块列表。")
    sample_chunks: list[ChunkSampleItem] = Field(default_factory=list, description="切块样例列表。")
