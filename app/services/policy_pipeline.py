from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.domain.policy import PolicyIdentityPolicy
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy_pipeline import (
    CleanedTextResult,
    ParsedTextResult,
    ParseRoutingResult,
    PersistenceResult,
    PipelineStageResult,
    PolicyPipelineRequest,
    PolicyPipelineResponse,
    RegisteredFileInfo,
    SectionSplitResult,
)
from app.services.policy_file_service import PolicyFileService
from app.services.policy_normalizer import PolicyFormatNormalizer
from app.services.policy_parser import PolicyParserService
from app.services.policy_section_splitter import PolicySectionSplitter
from app.services.policy_text_cleaner import PolicyTextCleaner


class PolicyPipelineService:
    """
    第一阶段制度入库流水线的应用服务编排器。

    当前 service 层按代码编排顺序约定如下：
    - 步骤 1：文件登记
    - 步骤 2：intake 校验
    - 步骤 3：格式标准化钩子
    - 步骤 4：解析器选择
    - 步骤 5：原文抽取
    - 步骤 6：文本清洗
    - 步骤 7：章节拆分
    - 步骤 8：document/version/section 一次性落库

    说明：
    - `policy_name_guess`、`derived_version_label` 属于辅助推导信息，
      发生在步骤 1 之后，但不单独占用一个步骤编号。
    - 步骤 3 是统一流水线里保留的标准化入口。
      当前 MVP 只允许 `.docx` / `.pdf`，所以大多数请求会直接 `skipped`。

    分层约定如下：
    - domain layer：业务规则与识别策略
    - application service：流程编排与阶段顺序控制
    - repository：持久化
    """

    def __init__(self, repository: PolicyRepository | None = None) -> None:
        self.repository = repository
        workspace_root = Path(settings.policy_pipeline_workspace)
        self.file_service = PolicyFileService()
        self.normalizer = PolicyFormatNormalizer(workspace_root=workspace_root)
        self.parser = PolicyParserService()
        self.cleaner = PolicyTextCleaner()
        self.section_splitter = PolicySectionSplitter()
        self.identity_policy = PolicyIdentityPolicy()

    def preview(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        """执行流水线，但不写库。"""
        return self._run(request=request, mode="preview", persist=False)

    def ingest(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        """执行流水线，并落库 document/version/section。"""
        if self.repository is None:
            raise RuntimeError("A repository is required for ingest mode.")
        return self._run(request=request, mode="ingest", persist=True)

    def _run(
        self,
        *,
        request: PolicyPipelineRequest,
        mode: str,
        persist: bool,
    ) -> PolicyPipelineResponse:
        """
        按固定顺序执行每个阶段，遇到致命失败即终止。

        这里优先返回结构化响应，而不是立刻抛异常，
        这样在 MVP 阶段更利于接口联调和人工排查。

        主流程顺序如下：
        1. 文件登记
        2. intake 校验
        3. 格式标准化
        4. 解析器选择
        5. 原文抽取
        6. 文本清洗
        7. 章节拆分
        8. 一次性落库
        """
        response = self._build_response(mode=mode, source_path=request.source_path)

        registered_file = self._register_source_file(
            response=response,
            source_path=request.source_path,
        )
        self._populate_identity_fields(
            response=response,
            request=request,
            registered_file=registered_file,
        )

        if not self._validate_intake(response=response, registered_file=registered_file):
            return response

        normalization = self._normalize_source(
            response=response,
            registered_file=registered_file,
        )
        if normalization is None:
            return response

        parse_routing = self._route_parser(
            response=response,
            source_path=normalization.normalized_path,
        )
        parsed_text = self._parse_text(
            response=response,
            source_path=normalization.normalized_path,
            parse_routing=parse_routing,
        )
        if parsed_text is None:
            return response

        # preview 可以暴露“疑似扫描件”提示，但 ingest 必须在任何写库前终止。
        if self._stop_before_persistence_for_scanned_pdf(
            response=response,
            persist=persist,
            parsed_text=parsed_text,
        ):
            return response

        cleaned_text = self._clean_text(
            response=response,
            parsed_text=parsed_text,
        )
        section_result = self._split_sections(
            response=response,
            cleaned_text=cleaned_text,
        )

        response.persistence = self._persist_if_needed(
            persist=persist,
            request=request,
            response=response,
            registered_file=registered_file,
            parse_routing=parse_routing,
            parsed_text=parsed_text,
            cleaned_text=cleaned_text,
            section_result=section_result,
        )
        self._record_persistence_stage(response=response, persist=persist)
        return response

    def _build_response(self, *, mode: str, source_path: str) -> PolicyPipelineResponse:
        """创建用于累计各阶段结果的响应对象。"""
        return PolicyPipelineResponse(
            mode=mode,
            source_path=source_path,
            stages=[],
        )

    def _register_source_file(
        self,
        *,
        response: PolicyPipelineResponse,
        source_path: str,
    ) -> RegisteredFileInfo:
        """阶段 1：收集源文件的不可变元数据。"""
        registered_file = self.file_service.register_file(source_path)
        response.registered_file = registered_file
        self._append_success_stage(
            response,
            "file_registration",
            "Source file metadata registered.",
        )
        return registered_file

    def _populate_identity_fields(
        self,
        *,
        response: PolicyPipelineResponse,
        request: PolicyPipelineRequest,
        registered_file: RegisteredFileInfo,
    ) -> None:
        """
        辅助推导制度名称和版本标签。

        这一步发生在步骤 1 之后、步骤 2 之前，
        用于让 preview/ingest 都能明确展示“准备如何入库”。
        """
        response.policy_name_guess = self.identity_policy.guess_policy_name(
            file_name=registered_file.file_name,
        )
        response.derived_version_label = self.identity_policy.build_version_label(
            explicit_label=request.version_label,
            modified_at_text=registered_file.source_modified_at.strftime("%Y%m%d"),
        )

    def _validate_intake(
        self,
        *,
        response: PolicyPipelineResponse,
        registered_file: RegisteredFileInfo,
    ) -> bool:
        """阶段 2：在解析前执行轻量级 intake 规则校验。"""
        validation = self.file_service.validate_intake(registered_file)
        response.validation = validation
        if not validation.is_allowed:
            self._append_failure_stage(
                response,
                "intake_validation",
                "; ".join(validation.warnings),
            )
            return False

        self._append_success_stage(
            response,
            "intake_validation",
            "File passed intake validation.",
        )
        return True

    def _normalize_source(
        self,
        *,
        response: PolicyPipelineResponse,
        registered_file: RegisteredFileInfo,
    ):
        """
        步骤 3：当格式有要求时，对源文件做标准化处理。

        当前 MVP 只允许 `.docx` / `.pdf`，
        因此这一步通常会返回 `skipped`，主要用于保留统一编排骨架。
        """
        normalization = self.normalizer.normalize(registered_file)
        response.normalization = normalization
        if normalization.status == "failed":
            self._append_failure_stage(
                response,
                "format_normalization",
                normalization.message,
            )
            return None

        self._append_stage(
            response,
            "format_normalization",
            normalization.status,
            normalization.message,
        )
        return normalization

    def _route_parser(
        self,
        *,
        response: PolicyPipelineResponse,
        source_path: str,
    ) -> ParseRoutingResult:
        """阶段 4：为标准化后的源文件选择解析器实现。"""
        parse_routing = self.parser.route_parser(source_path)
        response.parse_routing = parse_routing
        self._append_success_stage(
            response,
            "parse_routing",
            f"Selected parser: {parse_routing.parser_name}.",
        )
        return parse_routing

    def _parse_text(
        self,
        *,
        response: PolicyPipelineResponse,
        source_path: str,
        parse_routing: ParseRoutingResult,
    ) -> ParsedTextResult | None:
        """阶段 5：抽取原始文本及解析阶段的结构提示。"""
        parsed_text = self.parser.parse(
            source_path=source_path,
            parse_method=parse_routing.parse_method,
        )
        response.parsed_text = parsed_text
        if parsed_text.parser_status == "failed":
            self._append_failure_stage(
                response,
                "text_parsing",
                "; ".join(parsed_text.notes),
            )
            return None

        self._append_success_stage(
            response,
            "text_parsing",
            self._build_parsing_message(parsed_text),
        )
        return parsed_text

    def _build_parsing_message(self, parsed_text: ParsedTextResult) -> str:
        """构造 preview/ingest 响应里使用的解析阶段提示语。"""
        if not parsed_text.suspected_scanned:
            return "Raw text extracted successfully."
        if parsed_text.notes:
            return "; ".join(parsed_text.notes)
        return (
            "PDF looks scan-based in MVP; preview marks it, "
            "ingest stops before persistence."
        )

    def _stop_before_persistence_for_scanned_pdf(
        self,
        *,
        response: PolicyPipelineResponse,
        persist: bool,
        parsed_text: ParsedTextResult,
    ) -> bool:
        """在事务开始前阻断疑似扫描 PDF 的 ingest。"""
        if not parsed_text.suspected_scanned or not persist:
            return False

        response.persistence = PersistenceResult(
            persisted=False,
            message="Likely scanned PDF is not ingested in MVP.",
        )
        self._append_failure_stage(
            response,
            "document_persistence",
            "Likely scanned PDF is not ingested in MVP.",
        )
        return True

    def _clean_text(
        self,
        *,
        response: PolicyPipelineResponse,
        parsed_text: ParsedTextResult,
    ) -> CleanedTextResult:
        """阶段 6：规范空白字符，并移除保守可删的噪音。"""
        cleaned_text = self.cleaner.clean(parsed_text)
        response.cleaned_text = cleaned_text
        self._append_success_stage(
            response,
            "text_cleaning",
            "Text cleaned with conservative rules.",
        )
        return cleaned_text

    def _split_sections(
        self,
        *,
        response: PolicyPipelineResponse,
        cleaned_text: CleanedTextResult,
    ) -> SectionSplitResult:
        """阶段 7：把清洗后的文本拆成可落库的 section 记录。"""
        section_result = self.section_splitter.split(cleaned_text)
        response.section_result = section_result
        self._append_success_stage(
            response,
            "section_splitting",
            f"Generated {section_result.total_sections} sections.",
        )
        return section_result

    def _persist_if_needed(
        self,
        *,
        persist: bool,
        request: PolicyPipelineRequest,
        response: PolicyPipelineResponse,
        registered_file: RegisteredFileInfo,
        parse_routing: ParseRoutingResult,
        parsed_text: ParsedTextResult,
        cleaned_text: CleanedTextResult,
        section_result: SectionSplitResult,
    ) -> PersistenceResult:
        """步骤 8：在 ingest 模式下一次性落库 document/version/section 元数据。"""
        if not persist:
            return PersistenceResult(
                persisted=False,
                message="Preview mode: skipped database persistence.",
            )

        if self.repository is None:
            return PersistenceResult(
                persisted=False,
                message="No repository configured for ingest mode.",
            )

        policy_name = self._require_policy_name(response)
        version_label = self._require_version_label(response)

        # repository 负责持有 document/version/section 的单事务边界。
        persisted = self.repository.save_document_version_and_sections(
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
        )
        return PersistenceResult(
            persisted=True,
            document_id=persisted.document.id,
            version_id=persisted.version.id,
            version_seq=persisted.version.version_seq,
            version_label=persisted.version.version_label,
            section_count=len(persisted.sections),
            message="Persisted document, version, and split sections.",
        )

    def _require_policy_name(self, response: PolicyPipelineResponse) -> str:
        """确保进入持久化前，制度名称已经完成推导。"""
        if response.policy_name_guess is None:
            raise RuntimeError("Policy name is missing before persistence.")
        return response.policy_name_guess

    def _require_version_label(self, response: PolicyPipelineResponse) -> str:
        """确保进入持久化前，版本标签已经完成推导。"""
        if response.derived_version_label is None:
            raise RuntimeError("Version label is missing before persistence.")
        return response.derived_version_label

    def _record_persistence_stage(
        self,
        *,
        response: PolicyPipelineResponse,
        persist: bool,
    ) -> None:
        """在 preview/ingest 结束后补记最终持久化阶段结果。"""
        if response.persistence is None:
            raise RuntimeError("Persistence result is missing at the end of the pipeline.")

        status = "success" if response.persistence.persisted or not persist else "failed"
        self._append_stage(
            response,
            "document_persistence",
            status,
            response.persistence.message,
        )

    def _append_success_stage(
        self,
        response: PolicyPipelineResponse,
        stage: str,
        message: str,
    ) -> None:
        """记录成功阶段结果的快捷方法。"""
        self._append_stage(response, stage, "success", message)

    def _append_failure_stage(
        self,
        response: PolicyPipelineResponse,
        stage: str,
        message: str,
    ) -> None:
        """记录失败阶段结果的快捷方法。"""
        self._append_stage(response, stage, "failed", message)

    def _append_stage(
        self,
        response: PolicyPipelineResponse,
        stage: str,
        status: str,
        message: str,
    ) -> None:
        """向响应里追加一条阶段执行记录。"""
        response.stages.append(PipelineStageResult(stage=stage, status=status, message=message))
