from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.policy import PolicyDocument, PolicySection, PolicyVersion
from app.schemas.policy_pipeline import (
    CleanedTextResult,
    RegisteredFileInfo,
    SectionSplitItem,
)


@dataclass(slots=True)
class PersistedPolicyRecords:
    """Value object returned after document/version/section persistence."""

    document: PolicyDocument
    version: PolicyVersion
    sections: list[PolicySection]


class PolicyRepository:
    """Repository layer for policy-related database operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_document_version(
        self,
        *,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
        registered_file: RegisteredFileInfo,
        version_label: str,
        parse_method: str,
        parser_status: str,
        is_scanned: bool,
        raw_text: str,
        cleaned_text: CleanedTextResult,
    ) -> PersistedPolicyRecords:
        """
        Persist the source document root and its new version.

        This is the stage-7 repository entry point. We intentionally stop at the
        version layer so stage 8 can be retried independently later.
        """
        document = self._get_or_create_document(
            policy_name=policy_name,
            policy_category=policy_category,
            responsible_department=responsible_department,
        )
        version = self._create_version(
            document=document,
            registered_file=registered_file,
            version_label=version_label,
            parse_method=parse_method,
            parser_status=parser_status,
            is_scanned=is_scanned,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
        )
        document.latest_version_id = version.id
        if document.current_version_id is None:
            document.current_version_id = version.id
            version.version_status = "active"
            document.status = "active"

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        self.session.refresh(version)
        return PersistedPolicyRecords(document=document, version=version, sections=[])

    def replace_sections_for_version(
        self,
        *,
        version_id: int,
        sections: list[SectionSplitItem],
    ) -> list[PolicySection]:
        """
        Replace all sections for one already-persisted version.

        This is the stage-8 repository entry point. Keeping it separate from
        stage 7 avoids duplicate version creation when the splitter is rerun.
        """
        version = self.session.get(PolicyVersion, version_id)
        if version is None:
            raise ValueError(f"Policy version not found: {version_id}")

        persisted_sections = self._replace_sections(version=version, sections=sections)
        self.session.commit()
        return persisted_sections

    def _get_or_create_document(
        self,
        *,
        policy_name: str,
        policy_category: str,
        responsible_department: str | None,
    ) -> PolicyDocument:
        """
        Reuse an existing policy main document when name/category match.

        For the first engineering stage, this is a practical dedupe rule.
        Later we can evolve it to use policy_code or a formal business key.
        """
        statement = (
            select(PolicyDocument)
            .where(PolicyDocument.policy_name == policy_name)
            .where(PolicyDocument.policy_category == policy_category)
            .limit(1)
        )
        document = self.session.scalar(statement)
        if document is not None:
            if responsible_department and not document.responsible_department:
                document.responsible_department = responsible_department
            return document

        document = PolicyDocument(
            policy_name=policy_name,
            policy_category=policy_category,
            responsible_department=responsible_department,
            status="draft",
        )
        self.session.add(document)
        self.session.flush()
        return document

    def _create_version(
        self,
        *,
        document: PolicyDocument,
        registered_file: RegisteredFileInfo,
        version_label: str,
        parse_method: str,
        parser_status: str,
        is_scanned: bool,
        raw_text: str,
        cleaned_text: CleanedTextResult,
    ) -> PolicyVersion:
        """Create one concrete version row for the current source file."""
        current_max_seq = self.session.scalar(
            select(func.max(PolicyVersion.version_seq)).where(PolicyVersion.policy_id == document.id)
        )
        next_seq = (current_max_seq or 0) + 1

        version = PolicyVersion(
            policy_id=document.id,
            version_seq=next_seq,
            version_label=version_label,
            source_path=registered_file.source_path,
            file_name=registered_file.file_name,
            file_ext=registered_file.extension,
            file_hash=registered_file.sha256,
            is_scanned=is_scanned,
            parse_method=parse_method,
            raw_text=raw_text,
            clean_text=cleaned_text.clean_text,
            page_count=cleaned_text.page_count,
            parser_status=parser_status,
            version_status="draft",
        )
        self.session.add(version)
        self.session.flush()
        return version

    def _replace_sections(
        self,
        *,
        version: PolicyVersion,
        sections: list[SectionSplitItem],
    ) -> list[PolicySection]:
        """
        Replace all sections for the version with the latest split result.

        This keeps re-running the section splitter idempotent for one version.
        """
        self.session.execute(
            delete(PolicySection).where(PolicySection.version_id == version.id)
        )

        persisted_sections: list[PolicySection] = []
        for item in sections:
            section = PolicySection(
                version_id=version.id,
                parent_section_id=None,
                section_no=item.section_no,
                section_title=item.section_title,
                section_level=item.section_level,
                section_path=item.section_path,
                section_order=item.section_order,
                page_start=item.page_start,
                page_end=item.page_end,
                section_text=item.section_text,
                review_status="pending",
                metadata_json=item.metadata,
            )
            self.session.add(section)
            persisted_sections.append(section)

        self.session.flush()
        return persisted_sections
