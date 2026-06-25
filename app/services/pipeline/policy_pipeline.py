from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.domain.policy import PolicyIdentityPolicy
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import (
    ChunkSplitResult,
    CleanedTextResult,
    FormatNormalizationResult,
    ParsedTextResult,
    ParseRoutingResult,
    PersistenceResult,
    PipelineStageName,
    PipelineStageResult,
    PipelineStatus,
    PolicyPipelineRequest,
    PolicyPipelineResponse,
    RegisteredFileInfo,
    SectionSplitResult,
)
from app.services.step.policy_chunking import PolicyChunkingService
from app.services.step.policy_embedding import PolicyEmbeddingService
from app.services.step.policy_file_service import PolicyFileService
from app.services.step.policy_normalizer import PolicyFormatNormalizer
from app.services.step.policy_parser import PolicyParserService
from app.services.step.policy_section_splitter import PolicySectionSplitter
from app.services.step.policy_text_cleaner import PolicyTextCleaner


class PolicyPipelineService:
    """制度流水线编排服务，只负责编排步骤顺序。"""

    def __init__(self, repository: PolicyRepository | None = None) -> None:
        workspace_root = Path(settings.policy_pipeline_workspace)
        self.repository = repository
        self.file_service = PolicyFileService()
        self.normalizer = PolicyFormatNormalizer(workspace_root=workspace_root)
        self.parser = PolicyParserService()
        self.cleaner = PolicyTextCleaner()
        self.section_splitter = PolicySectionSplitter()
        self.chunking_service = PolicyChunkingService()
        self.identity_policy = PolicyIdentityPolicy()

    def preview(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        return self._run(request=request, mode="preview", persist=False)

    def ingest(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        if self.repository is None:
            raise RuntimeError("入库模式必须提供仓储实例。")
        return self._run(request=request, mode="ingest", persist=True)

    def _run(
        self,
        *,
        request: PolicyPipelineRequest,
        mode: str,
        persist: bool,
    ) -> PolicyPipelineResponse:
        response = PolicyPipelineResponse(
            mode=mode,
            source_path=request.source_path,
            stages=[],
        )

        # 步骤 1-2：文件登记、制度名称推导、准入校验。
        registered_file = self.file_service.register_file(request.source_path)
        response.registered_file = registered_file
        self._append_success_stage(response, "file_registration", "已完成源文件登记。")

        response.policy_name_guess = self.identity_policy.guess_policy_name(
            file_name=registered_file.file_name,
        )
        response.derived_version_label = self.identity_policy.build_version_label(
            explicit_label=request.version_label,
            modified_at_text=registered_file.source_modified_at.strftime("%Y%m%d"),
        )

        validation = self.file_service.validate_intake(registered_file)
        response.validation = validation
        if not validation.is_allowed:
            self._append_failure_stage(
                response,
                "intake_validation",
                self._join_messages(validation.warnings, "文件未通过准入校验。"),
            )
            return response
        self._append_success_stage(response, "intake_validation", "文件通过准入校验。")

        # 步骤 3-5：格式归一化、解析路由、文本解析。
        normalization = self.normalizer.normalize(registered_file)
        response.normalization = normalization
        if normalization.status == "failed":
            self._append_failure_stage(
                response,
                "format_normalization",
                normalization.message,
            )
            return response
        self._append_stage(
            response,
            "format_normalization",
            normalization.status,
            normalization.message,
        )

        parse_routing = self.parser.route_parser(normalization.normalized_path)
        response.parse_routing = parse_routing
        self._append_success_stage(
            response,
            "parse_routing",
            f"已选择解析器：{parse_routing.parser_name}。",
        )

        parsed_text = self.parser.parse(
            source_path=normalization.normalized_path,
            parse_method=parse_routing.parse_method,
        )
        response.parsed_text = parsed_text
        if parsed_text.parser_status == "failed":
            self._append_failure_stage(
                response,
                "text_parsing",
                self._join_messages(parsed_text.notes, "文本解析失败。"),
            )
            return response
        self._append_success_stage(
            response,
            "text_parsing",
            self._build_parsing_message(parsed_text),
        )

        if parsed_text.suspected_scanned and persist:
            message = "疑似扫描版 PDF，当前版本暂不支持直接正式入库。"
            response.persistence = PersistenceResult(
                persisted=False,
                message=message,
            )
            self._append_failure_stage(response, "document_persistence", message)
            return response

        # 步骤 6-8：文本清洗、章节拆分、切块摘要。
        cleaned_text = self.cleaner.clean(parsed_text)
        response.cleaned_text = cleaned_text
        self._append_success_stage(response, "text_cleaning", "已完成文本清洗。")

        section_result = self.section_splitter.split(cleaned_text)
        response.section_result = section_result
        self._append_success_stage(
            response,
            "section_splitting",
            f"已拆分出 {section_result.total_sections} 个章节。",
        )

        chunk_result = self.chunking_service.split(section_result)
        response.chunk_result = chunk_result.model_copy(update={"chunks": []})
        self._append_success_stage(
            response,
            "chunk_splitting",
            f"已生成 {chunk_result.total_chunks} 个切块。",
        )

        if not persist:
            self._append_stage(
                response,
                "embedding_generation",
                "skipped",
                "预览模式不生成向量。",
            )
            response.persistence = PersistenceResult(
                persisted=False,
                chunk_count=chunk_result.total_chunks,
                message="预览模式不写入数据库。",
            )
            self._append_stage(
                response,
                "chunk_persistence",
                "skipped",
                "预览模式不写入切块。",
            )
            self._record_persistence_stage(response=response, persist=False)
            return response

        # 步骤 9-11：向量生成、切块入库、文档入库收尾。
        embedding_service = PolicyEmbeddingService()
        embedded_chunks = embedding_service.embed_chunks(chunk_result.chunks)
        self._append_success_stage(
            response,
            "embedding_generation",
            f"已为 {len(embedded_chunks)} 个切块生成向量。",
        )

        embedded_chunk_result = chunk_result.model_copy(update={"chunks": embedded_chunks})
        response.persistence = self._persist(
            request=request,
            response=response,
            registered_file=registered_file,
            parse_routing=parse_routing,
            parsed_text=parsed_text,
            cleaned_text=cleaned_text,
            section_result=section_result,
            chunk_result=embedded_chunk_result,
        )
        self._append_success_stage(
            response,
            "chunk_persistence",
            f"已写入 {response.persistence.chunk_count} 个切块及其向量。",
        )
        self._record_persistence_stage(response=response, persist=True)
        return response

    def _build_parsing_message(self, parsed_text: ParsedTextResult) -> str:
        if not parsed_text.suspected_scanned:
            return "已完成原始文本提取。"
        return self._join_messages(
            parsed_text.notes,
            "疑似扫描版 PDF，预览会保留提示，入库会在落库前停止。",
        )

    def _persist(
        self,
        *,
        request: PolicyPipelineRequest,
        response: PolicyPipelineResponse,
        registered_file: RegisteredFileInfo,
        parse_routing: ParseRoutingResult,
        parsed_text: ParsedTextResult,
        cleaned_text: CleanedTextResult,
        section_result: SectionSplitResult,
        chunk_result: ChunkSplitResult,
    ) -> PersistenceResult:
        if self.repository is None:
            raise RuntimeError("入库模式未配置仓储实例。")

        policy_name = response.policy_name_guess
        if not policy_name:
            raise RuntimeError("落库前缺少制度名称。")

        version_label = response.derived_version_label
        if not version_label:
            raise RuntimeError("落库前缺少版本标签。")

        persisted = self.repository.save_document_version_sections_and_chunks(
            policy_name=policy_name,
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
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

    def _record_persistence_stage(
        self,
        *,
        response: PolicyPipelineResponse,
        persist: bool,
    ) -> None:
        if response.persistence is None:
            raise RuntimeError("流水线结束时缺少落库结果。")

        status: PipelineStatus = (
            "success" if response.persistence.persisted or not persist else "failed"
        )
        self._append_stage(
            response,
            "document_persistence",
            status,
            response.persistence.message,
        )

    def _join_messages(self, messages: list[str], fallback: str) -> str:
        normalized = [message.strip() for message in messages if message.strip()]
        if not normalized:
            return fallback
        return "；".join(normalized)

    def _append_success_stage(
        self,
        response: PolicyPipelineResponse,
        stage: PipelineStageName,
        message: str,
    ) -> None:
        self._append_stage(response, stage, "success", message)

    def _append_failure_stage(
        self,
        response: PolicyPipelineResponse,
        stage: PipelineStageName,
        message: str,
    ) -> None:
        self._append_stage(response, stage, "failed", message)

    def _append_stage(
        self,
        response: PolicyPipelineResponse,
        stage: PipelineStageName,
        status: PipelineStatus,
        message: str,
    ) -> None:
        response.stages.append(
            PipelineStageResult(
                stage=stage,
                status=status,
                message=message,
            )
        )
