from __future__ import annotations

from pathlib import Path
import subprocess

from app.schemas.policy_pipeline import FormatNormalizationResult, RegisteredFileInfo


class PolicyFormatNormalizer:
    """Normalize legacy .doc files into standard .docx files."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def normalize(self, registered_file: RegisteredFileInfo) -> FormatNormalizationResult:
        """
        Convert a legacy Word document into a `.docx` derivative.

        The original source file is never overwritten. We keep a normalized copy
        so later parsing stages always consume a predictable format.
        """
        if registered_file.extension != ".doc":
            return FormatNormalizationResult(
                status="skipped",
                source_path=registered_file.source_path,
                normalized_path=registered_file.source_path,
                output_extension=registered_file.extension,
                converter="none",
                message="Normalization is only required for legacy .doc files.",
            )

        source_path = Path(registered_file.source_path)
        output_dir = self.workspace_root / "normalized" / registered_file.sha256[:12]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source_path.stem}.docx"

        if output_path.exists():
            return FormatNormalizationResult(
                status="success",
                source_path=registered_file.source_path,
                normalized_path=str(output_path),
                output_extension=".docx",
                converter="powershell-word-com",
                message="Reused an existing normalized .docx file.",
            )

        try:
            self._convert_via_word_com(source_path=source_path, output_path=output_path)
        except Exception as exc:
            return FormatNormalizationResult(
                status="failed",
                source_path=registered_file.source_path,
                normalized_path=str(output_path),
                output_extension=".docx",
                converter="powershell-word-com",
                message=str(exc),
            )

        return FormatNormalizationResult(
            status="success",
            source_path=registered_file.source_path,
            normalized_path=str(output_path),
            output_extension=".docx",
            converter="powershell-word-com",
            message="Converted legacy .doc into normalized .docx.",
        )

    def _convert_via_word_com(self, *, source_path: Path, output_path: Path) -> None:
        """
        Use local Microsoft Word COM automation for format conversion on Windows.

        This is intentionally isolated in one method because it depends on the host
        environment. If you later choose LibreOffice instead, you only need to
        replace this adapter.
        """
        script = f"""
$ErrorActionPreference = 'Stop'
$source = '{str(source_path).replace("'", "''")}'
$target = '{str(output_path).replace("'", "''")}'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$document = $word.Documents.Open($source)
$document.SaveAs([ref] $target, [ref] 16)
$document.Close()
$word.Quit()
""".strip()
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "Unknown conversion error."
            raise RuntimeError(f"Failed to convert .doc to .docx: {stderr}")
