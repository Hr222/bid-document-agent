from __future__ import annotations

from pathlib import Path
from time import perf_counter

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.policy import PolicyIdentityPolicy
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import (
    PersistenceResult,
    PolicyPipelineRequest,
    PolicyPipelineResponse,
)
from app.services.pipeline.context import PipelineContext, PipelineMode
from app.services.pipeline.persistence_service import PolicyPersistenceService
from app.services.pipeline.response_builder import PipelineResponseBuilder
from app.services.step.policy_chunking import PolicyChunkingService
from app.services.step.policy_embedding import PolicyEmbeddingService
from app.services.step.policy_file_service import PolicyFileService
from app.services.step.policy_normalizer import PolicyFormatNormalizer
from app.services.step.policy_parser import PolicyParserService
from app.services.step.policy_section_splitter import PolicySectionSplitter
from app.services.step.policy_text_cleaner import PolicyTextCleaner

logger = get_logger("app.pipeline.policy")


class PolicyPipelineService:
    """编排制度文档处理流水线。"""

    def __init__(self, repository: PolicyRepository | None = None) -> None:
        workspace_root = Path(settings.policy_pipeline_workspace)
        self.repository = repository
        self.persistence_service = (
            PolicyPersistenceService(repository) if repository is not None else None
        )
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
        mode: PipelineMode,
        persist: bool,
    ) -> PolicyPipelineResponse:
        context = PipelineContext(request=request, mode=mode, persist=persist)
        builder = PipelineResponseBuilder(context)
        logger.info(
            "Pipeline started mode=%s persist=%s source_path=%s category=%s",
            mode,
            persist,
            request.source_path,
            request.policy_category,
        )

        stages = (
            self._register_file,
            self._validate_intake,
            self._normalize,
            self._route_parser,
            self._parse_text,
            self._guard_ingest_eligibility,
            self._clean_text,
            self._split_sections,
            self._split_chunks,
            self._embed_if_needed,
            self._persist_if_needed,
        )
        for stage in stages:
            stage_name = stage.__name__.removeprefix("_")
            started = perf_counter()
            logger.info("Pipeline stage started mode=%s stage=%s", mode, stage_name)
            try:
                stage(context, builder)
            except Exception:
                duration_ms = (perf_counter() - started) * 1000
                logger.exception(
                    "Pipeline stage failed mode=%s stage=%s duration_ms=%.2f",
                    mode,
                    stage_name,
                    duration_ms,
                )
                raise

            duration_ms = (perf_counter() - started) * 1000
            logger.info(
                "Pipeline stage finished mode=%s stage=%s stop_requested=%s duration_ms=%.2f",
                mode,
                stage_name,
                context.stop_requested,
                duration_ms,
            )
            if context.stop_requested:
                logger.warning("Pipeline stopped early mode=%s stage=%s", mode, stage_name)
                break

        response = builder.build()
        logger.info(
            "Pipeline finished mode=%s stage_count=%s persisted=%s source_path=%s",
            mode,
            len(response.stages),
            response.persistence.persisted if response.persistence is not None else False,
            request.source_path,
        )
        return response

    def _register_file(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        registered_file = self.file_service.register_file(context.request.source_path)
        builder.set_registered_file(registered_file)
        builder.set_policy_identity(
            policy_name_guess=self.identity_policy.guess_policy_name(
                file_name=registered_file.file_name,
            ),
            derived_version_label=self.identity_policy.build_version_label(
                explicit_label=context.request.version_label,
                modified_at_text=registered_file.source_modified_at.strftime("%Y%m%d"),
            ),
        )
        builder.success("file_registration", "已完成源文件登记。")

    def _validate_intake(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.registered_file is None:
            raise RuntimeError("执行准入校验前缺少文件登记结果。")

        validation = self.file_service.validate_intake(context.registered_file)
        builder.set_validation(validation)
        if not validation.is_allowed:
            builder.failed(
                "intake_validation",
                builder.join_messages(validation.warnings, "文件未通过准入校验。"),
                stop=True,
            )
            return
        builder.success("intake_validation", "文件通过准入校验。")

    def _normalize(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.registered_file is None:
            raise RuntimeError("执行格式归一化前缺少文件登记结果。")

        normalization = self.normalizer.normalize(context.registered_file)
        builder.set_normalization(normalization)
        if normalization.status == "failed":
            builder.failed("format_normalization", normalization.message, stop=True)
            return
        if normalization.status == "skipped":
            builder.skipped("format_normalization", normalization.message)
            return
        builder.success("format_normalization", normalization.message)

    def _route_parser(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.normalization is None:
            raise RuntimeError("执行解析器选择前缺少格式归一化结果。")

        parse_routing = self.parser.route_parser(context.normalization.normalized_path)
        builder.set_parse_routing(parse_routing)
        builder.success("parse_routing", f"已选择解析器：{parse_routing.parser_name}。")

    def _parse_text(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.normalization is None:
            raise RuntimeError("执行文本解析前缺少格式归一化结果。")
        if context.parse_routing is None:
            raise RuntimeError("执行文本解析前缺少解析器选择结果。")

        parsed_text = self.parser.parse(
            source_path=context.normalization.normalized_path,
            parse_method=context.parse_routing.parse_method,
        )
        builder.set_parsed_text(parsed_text)
        if parsed_text.parser_status == "failed":
            builder.failed(
                "text_parsing",
                builder.join_messages(parsed_text.notes, "文本解析失败。"),
                stop=True,
            )
            return
        builder.success("text_parsing", builder.parsing_message(parsed_text))

    def _guard_ingest_eligibility(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if not context.persist or context.parsed_text is None:
            return
        if not context.parsed_text.suspected_scanned:
            return

        message = "疑似扫描版 PDF，入库前终止，请先确认 OCR 或解析质量。"
        builder.set_persistence(
            PersistenceResult(
                persisted=False,
                message=message,
            )
        )
        builder.failed("document_persistence", message, stop=True)

    def _clean_text(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.parsed_text is None:
            raise RuntimeError("执行文本清洗前缺少文本解析结果。")

        cleaned_text = self.cleaner.clean(context.parsed_text)
        builder.set_cleaned_text(cleaned_text)
        builder.success("text_cleaning", "已完成文本清洗。")

    def _split_sections(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.cleaned_text is None:
            raise RuntimeError("执行章节拆分前缺少文本清洗结果。")

        section_result = self.section_splitter.split(context.cleaned_text)
        builder.set_section_result(section_result)
        builder.success(
            "section_splitting",
            f"已拆分出 {section_result.total_sections} 个章节。",
        )

    def _split_chunks(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.section_result is None:
            raise RuntimeError("执行切块前缺少章节拆分结果。")

        chunk_result = self.chunking_service.split(context.section_result)
        logger.info(
            "Chunk splitting result source_path=%s total_sections=%s total_chunks=%s sample_chunks=%s",
            context.request.source_path,
            context.section_result.total_sections,
            chunk_result.total_chunks,
            len(chunk_result.sample_chunks),
        )
        builder.set_chunk_result(chunk_result)
        builder.success("chunk_splitting", f"已生成 {chunk_result.total_chunks} 个切块。")

    def _embed_if_needed(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.chunk_result is None:
            raise RuntimeError("执行向量生成前缺少切块结果。")

        if not context.persist:
            builder.skipped("embedding_generation", "预览模式不生成向量。")
            return

        embedding_service = PolicyEmbeddingService()
        logger.info(
            "Embedding stage requested source_path=%s total_chunks=%s",
            context.request.source_path,
            context.chunk_result.total_chunks,
        )
        embedded_chunks = embedding_service.embed_chunks(context.chunk_result.chunks)
        embedded_chunk_result = context.chunk_result.model_copy(update={"chunks": embedded_chunks})
        builder.set_chunk_result(embedded_chunk_result)
        builder.success(
            "embedding_generation",
            f"已为 {len(embedded_chunks)} 个切块生成向量。",
        )

    def _persist_if_needed(
        self,
        context: PipelineContext,
        builder: PipelineResponseBuilder,
    ) -> None:
        if context.chunk_result is None:
            raise RuntimeError("执行落库前缺少切块结果。")

        if not context.persist:
            builder.set_persistence(
                PersistenceResult(
                    persisted=False,
                    chunk_count=context.chunk_result.total_chunks,
                    message="预览模式不写入数据库。",
                )
            )
            builder.skipped("chunk_persistence", "预览模式跳过切块落库。")
            builder.record_persistence_stage()
            return

        if self.persistence_service is None:
            raise RuntimeError("入库模式缺少持久化服务。")

        persistence = self.persistence_service.persist(context)
        logger.info(
            "Chunk persistence result source_path=%s document_id=%s version_id=%s section_count=%s chunk_count=%s",
            context.request.source_path,
            persistence.document_id,
            persistence.version_id,
            persistence.section_count,
            persistence.chunk_count,
        )
        builder.set_persistence(persistence)
        builder.success(
            "chunk_persistence",
            f"已写入 {persistence.chunk_count} 个切块及其向量。",
        )
        builder.record_persistence_stage()
