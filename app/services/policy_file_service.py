from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from app.domain.policy import PolicyIntakePolicy
from app.schemas.policy_pipeline import IntakeValidationResult, RegisteredFileInfo


class PolicyFileService:
    """Handle source file registration and delegate intake rules to the domain."""

    def __init__(self, intake_policy: PolicyIntakePolicy | None = None) -> None:
        self.intake_policy = intake_policy or PolicyIntakePolicy()

    def register_file(self, source_path: str) -> RegisteredFileInfo:
        """
        Read immutable source metadata.

        This corresponds to step 1 in the pipeline and should not modify any file.
        """
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file does not exist: {source_path}")
        if not path.is_file():
            raise IsADirectoryError(f"Source path is not a file: {source_path}")

        stat = path.stat()
        return RegisteredFileInfo(
            source_path=str(path),
            file_name=path.name,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            sha256=self._hash_file(path),
            source_modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

    def validate_intake(self, registered_file: RegisteredFileInfo) -> IntakeValidationResult:
        """
        Run lightweight gate checks before parsing.

        Business admission rules belong to the domain policy. The service only
        converts the domain decision into the pipeline DTO used by the API layer.
        """
        decision = self.intake_policy.decide(
            file_name=registered_file.file_name,
            extension=registered_file.extension,
            size_bytes=registered_file.size_bytes,
        )
        return IntakeValidationResult(
            is_allowed=decision.is_allowed,
            detected_file_kind=decision.detected_file_kind,
            needs_normalization=decision.needs_normalization,
            recommended_parse_method=decision.recommended_parse_method,
            warnings=decision.warnings,
        )

    def _hash_file(self, path: Path) -> str:
        """Calculate a stable SHA-256 hash for dedupe and traceability."""
        digest = sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
