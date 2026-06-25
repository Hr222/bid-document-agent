from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile


@dataclass(slots=True)
class StagedUpload:
    upload_id: str
    file_name: str
    stored_path: str
    size_bytes: int


class PolicyUploadService:
    """Handle temporary storage for single-file upload preview/ingest flows."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.upload_root = workspace_root / "uploads"
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def stage_upload(self, upload: UploadFile) -> StagedUpload:
        file_name = Path(upload.filename or "").name
        if not file_name:
            raise ValueError("上传文件必须包含文件名。")

        upload_id = uuid.uuid4().hex
        target_dir = self.upload_root / upload_id
        target_dir.mkdir(parents=True, exist_ok=False)
        target_path = target_dir / file_name

        upload.file.seek(0)
        with target_path.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)

        size_bytes = target_path.stat().st_size
        if size_bytes <= 0:
            target_path.unlink(missing_ok=True)
            raise ValueError("上传文件不能为空。")

        return StagedUpload(
            upload_id=upload_id,
            file_name=file_name,
            stored_path=str(target_path),
            size_bytes=size_bytes,
        )

    def resolve_upload(self, upload_id: str) -> str:
        normalized_id = upload_id.strip()
        if not normalized_id:
            raise ValueError("upload_id 不能为空。")

        target_dir = self.upload_root / normalized_id
        if not target_dir.exists() or not target_dir.is_dir():
            raise FileNotFoundError(f"upload_id 对应的上传文件不存在：{upload_id}")

        files = [path for path in target_dir.iterdir() if path.is_file()]
        if not files:
            raise FileNotFoundError(f"未找到 upload_id 对应的暂存文件：{upload_id}")
        if len(files) > 1:
            raise RuntimeError(f"upload_id 对应了多个暂存文件：{upload_id}")

        return str(files[0])
