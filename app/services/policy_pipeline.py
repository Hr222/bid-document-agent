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
)
from app.services.policy_file_service import PolicyFileService
from app.services.policy_normalizer import PolicyFormatNormalizer
from app.services.policy_parser import PolicyParserService
from app.services.policy_section_splitter import PolicySectionSplitter
from app.services.policy_text_cleaner import PolicyTextCleaner


class PolicyPipelineService:
    """
    Application service that orchestrates steps 1-8 of the policy pipeline.

    The rule of thumb is:
    - domain layer: business rules and recognition policies
    - application service: orchestration and stage ordering
    - repository: persistence
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
        """Run the pipeline without writing to the database."""
        return self._run(request=request, mode="preview", persist=False)

    def ingest(self, request: PolicyPipelineRequest) -> PolicyPipelineResponse:
        """Run the pipeline and persist document/version/section records."""
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
        Execute each pipeline stage in order and stop on first fatal failure.

        Returning a structured response instead of raising immediately makes the
        API easier to inspect during early engineering and manual debugging.
        """
        response = PolicyPipelineResponse(mode=mode, source_path=request.source_path, stages=[])

        registered_file = self.file_service.register_file(request.source_path)
        response.registered_file = registered_file
        self._append_stage(response, "file_registration", "success", "Source file metadata registered.")

        validation = self.file_service.validate_intake(registered_file)
        response.validation = validation
        if not validation.is_allowed:
            self._append_stage(response, "intake_validation", "failed", "; ".join(validation.warnings))
            return response
        self._append_stage(response, "intake_validation", "success", "File passed intake validation.")

        normalization = self.normalizer.normalize(registered_file)
        response.normalization = normalization
        if normalization.status == "failed":
            self._append_stage(response, "format_normalization", "failed", normalization.message)
            return response
        self._append_stage(response, "format_normalization", normalization.status, normalization.message)

        parse_source_path = normalization.normalized_path
        parse_routing = self.parser.route_parser(parse_source_path)
        response.parse_routing = parse_routing
        self._append_stage(response, "parse_routing", "success", f"Selected parser: {parse_routing.parser_name}.")

        parsed_text = self.parser.parse(source_path=parse_source_path, parse_method=parse_routing.parse_method)
        response.parsed_text = parsed_text
        if parsed_text.parser_status == "failed":
            self._append_stage(response, "text_parsing", "failed", "; ".join(parsed_text.notes))
            return response
        self._append_stage(response, "text_parsing", "success", "Raw text extracted successfully.")

        cleaned_text = self.cleaner.clean(parsed_text)
        response.cleaned_text = cleaned_text
        self._append_stage(response, "text_cleaning", "success", "Text cleaned with conservative rules.")

        persistence_result = self._persist_if_needed(
            persist=persist,
            request=request,
            registered_file=registered_file,
            parse_routing=parse_routing,
            parsed_text=parsed_text,
            cleaned_text=cleaned_text,
        )
        response.persistence = persistence_result
        self._append_stage(
            response,
            "document_persistence",
            "success" if persistence_result.persisted or not persist else "failed",
            persistence_result.message,
        )
        if persist and not persistence_result.persisted:
            return response

        section_result = self.section_splitter.split(cleaned_text)
        response.section_result = section_result

        if persist and self.repository is not None and persistence_result.version_id is not None:
            self.repository.replace_sections_for_version(
                version_id=persistence_result.version_id,
                sections=section_result.sections,
            )
            response.persistence = PersistenceResult(
                persisted=True,
                document_id=persistence_result.document_id,
                version_id=persistence_result.version_id,
                version_seq=persistence_result.version_seq,
                version_label=persistence_result.version_label,
                message="Persisted document, version, and split sections.",
            )

        self._append_stage(
            response,
            "section_splitting",
            "success",
            f"Generated {section_result.total_sections} sections.",
        )
        return response

    def _persist_if_needed(
        self,
        *,
        persist: bool,
        request: PolicyPipelineRequest,
        registered_file: RegisteredFileInfo,
        parse_routing: ParseRoutingResult,
        parsed_text: ParsedTextResult,
        cleaned_text: CleanedTextResult,
    ) -> PersistenceResult:
        """
        Persist document/version metadata when ingest mode is enabled.

        We intentionally delay section persistence until after splitting, but we
        still report stage 7 here so the API mirrors the conceptual pipeline.
        """
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

        persisted = self.repository.save_document_version(
            policy_name=self.identity_policy.guess_policy_name(file_name=registered_file.file_name),
            policy_category=request.policy_category,
            responsible_department=request.responsible_department,
            registered_file=registered_file,
            version_label=self.identity_policy.build_version_label(
                explicit_label=request.version_label,
                modified_at_text=registered_file.source_modified_at.strftime("%Y%m%d"),
            ),
            parse_method=parse_routing.parse_method,
            parser_status=parsed_text.parser_status,
            is_scanned=parse_routing.suspected_scanned_pdf,
            raw_text=parsed_text.raw_text,
            cleaned_text=cleaned_text,
        )
        return PersistenceResult(
            persisted=True,
            document_id=persisted.document.id,
            version_id=persisted.version.id,
            version_seq=persisted.version.version_seq,
            version_label=persisted.version.version_label,
            message="Persisted document and version metadata.",
        )

    def _append_stage(
        self,
        response: PolicyPipelineResponse,
        stage: str,
        status: str,
        message: str,
    ) -> None:
        """Append one stage execution result to the response trace."""
        response.stages.append(PipelineStageResult(stage=stage, status=status, message=message))
