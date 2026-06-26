from __future__ import annotations

from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import (
    ChunkSplitResult,
    CleanedTextResult,
    ParsedTextResult,
    ParseRoutingResult,
    PersistenceResult,
    RegisteredFileInfo,
    SectionSplitResult,
)
from app.services.pipeline.context import PipelineContext


class PolicyPersistenceService:
    def __init__(self, repository: PolicyRepository) -> None:
        self.repository = repository

    def persist(self, context: PipelineContext) -> PersistenceResult:
        policy_name = context.policy_name_guess
        if not policy_name:
            raise RuntimeError("落库前缺少制度名称。")

        version_label = context.derived_version_label
        if not version_label:
            raise RuntimeError("落库前缺少版本标签。")

        registered_file = self._require_registered_file(context.registered_file)
        parse_routing = self._require_parse_routing(context.parse_routing)
        parsed_text = self._require_parsed_text(context.parsed_text)
        cleaned_text = self._require_cleaned_text(context.cleaned_text)
        section_result = self._require_section_result(context.section_result)
        chunk_result = self._require_chunk_result(context.chunk_result)

        persisted = self.repository.save_document_version_sections_and_chunks(
            policy_name=policy_name,
            policy_category=context.request.policy_category,
            responsible_department=context.request.responsible_department,
            registered_file=registered_file,
            version_label=version_label,
            parse_method=parse_routing.parse_method,
            parser_status=parsed_text.parser_status,
            is_scanned=parsed_text.suspected_scanned,
            raw_text=parsed_text.raw_text,
            cleaned_text=cleaned_text,
            sections=section_result.sections,
            chunks=chunk_result.chunks,
        )
        return PersistenceResult(
            persisted=True,
            document_id=persisted.document.id,
            version_id=persisted.version.id,
            version_seq=persisted.version.version_seq,
            version_label=persisted.version.version_label,
            section_count=len(persisted.sections),
            chunk_count=len(persisted.chunks),
            message="已完成制度文档、版本、章节、切块和向量入库。",
        )

    def _require_registered_file(
        self,
        registered_file: RegisteredFileInfo | None,
    ) -> RegisteredFileInfo:
        if registered_file is None:
            raise RuntimeError("落库前缺少文件登记结果。")
        return registered_file

    def _require_parse_routing(
        self,
        parse_routing: ParseRoutingResult | None,
    ) -> ParseRoutingResult:
        if parse_routing is None:
            raise RuntimeError("落库前缺少解析路由结果。")
        return parse_routing

    def _require_parsed_text(self, parsed_text: ParsedTextResult | None) -> ParsedTextResult:
        if parsed_text is None:
            raise RuntimeError("落库前缺少文本解析结果。")
        return parsed_text

    def _require_cleaned_text(
        self,
        cleaned_text: CleanedTextResult | None,
    ) -> CleanedTextResult:
        if cleaned_text is None:
            raise RuntimeError("落库前缺少文本清洗结果。")
        return cleaned_text

    def _require_section_result(
        self,
        section_result: SectionSplitResult | None,
    ) -> SectionSplitResult:
        if section_result is None:
            raise RuntimeError("落库前缺少章节拆分结果。")
        return section_result

    def _require_chunk_result(self, chunk_result: ChunkSplitResult | None) -> ChunkSplitResult:
        if chunk_result is None:
            raise RuntimeError("落库前缺少切块结果。")
        return chunk_result
