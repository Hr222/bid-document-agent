from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path

from app.schemas import (
    ParsedBlock,
    ParsedDocumentResult,
    ParseRoutingResult,
)

_CUSTOM_IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpe": "image/jpeg",
    ".jp2": "image/jp2",
    ".jpx": "image/jp2",
}


class PolicyParserService:
    """
    负责制度文件的结构化解析阶段。
    - 步骤 4：解析器选择
    - 步骤 5：解析为有序 block 流
    """

    def route_parser(self, source_path: str) -> ParseRoutingResult:
        path = Path(source_path)
        suffix = path.suffix.lower()

        if suffix == ".docx":
            return ParseRoutingResult(
                parser_name="DocxBlockParser",
                parse_method="direct",
                suspected_scanned_pdf=False,
                notes=[],
            )
        if suffix == ".pdf":
            return ParseRoutingResult(
                parser_name="PdfBlockParser",
                parse_method="direct",
                suspected_scanned_pdf=False,
                notes=[],
            )

        raise ValueError(f"当前文件类型未配置解析器：{suffix}")

    def parse_document(self, *, source_path: str, parse_method: str) -> ParsedDocumentResult:
        if parse_method != "direct":
            raise ValueError(f"当前只支持 direct 路由进入结构化解析：{parse_method}")

        suffix = Path(source_path).suffix.lower()
        if suffix == ".docx":
            return self._parse_docx(source_path)
        if suffix == ".pdf":
            return self._parse_pdf(source_path)
        raise ValueError(f"不支持的文件类型：{suffix}")

    def _parse_docx(self, source_path: str) -> ParsedDocumentResult:
        try:
            from docx import Document
            from docx.document import Document as DocumentObject
            from docx.table import Table
            from docx.text.paragraph import Paragraph
        except ImportError as exc:
            raise RuntimeError("缺少依赖：未安装 python-docx。") from exc

        document = Document(source_path)
        blocks: list[ParsedBlock] = []

        relation_by_rid = {
            rel_id: rel for rel_id, rel in document.part.rels.items() if "image" in rel.reltype
        }

        def append_block(
            *,
            block_type: str,
            text: str | None,
            metadata: dict | None = None,
            layout_hint: dict | None = None,
        ) -> None:
            blocks.append(
                ParsedBlock(
                    block_id=uuid.uuid4().hex,
                    order=len(blocks),
                    page_no=None,
                    block_type=block_type,
                    source="direct",
                    text=text,
                    metadata=metadata or {},
                    layout_hint=layout_hint or {},
                )
            )

        def iter_block_items(parent):
            parent_elm = parent.element.body if isinstance(parent, DocumentObject) else parent._tc
            for child in parent_elm.iterchildren():
                if child.tag.endswith("}p"):
                    yield Paragraph(child, parent)
                elif child.tag.endswith("}tbl"):
                    yield Table(child, parent)

        for item in iter_block_items(document):
            if isinstance(item, Paragraph):
                paragraph_text = item.text.strip()
                image_rel_ids: list[str] = []
                for drawing in item._element.xpath(".//*[local-name()='blip']"):
                    rel_id = drawing.get(
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                    )
                    if rel_id:
                        image_rel_ids.append(rel_id)

                if paragraph_text:
                    append_block(block_type="text", text=paragraph_text)

                for rel_id in image_rel_ids:
                    relation = relation_by_rid.get(rel_id)
                    image_bytes = relation.target_part.blob if relation is not None else b""
                    image_name = (
                        Path(str(relation.target_part.partname)).name if relation is not None else None
                    )
                    image_media_type = (
                        getattr(relation.target_part, "content_type", None) if relation is not None else None
                    )
                    append_block(
                        block_type="image",
                        text=None,
                        metadata={
                            "container": "paragraph",
                            "image_rel_id": rel_id,
                            "image_name": image_name,
                            "image_media_type": image_media_type,
                            "image_bytes": image_bytes.hex(),
                        },
                    )
            else:
                table_lines: list[str] = []
                for row in item.rows:
                    row_values = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_values:
                        table_lines.append(" | ".join(row_values))
                if table_lines:
                    append_block(
                        block_type="table",
                        text="\n".join(table_lines),
                        metadata={"row_count": len(table_lines)},
                    )

        return ParsedDocumentResult(
            parser_status="parsed",
            source_path=source_path,
            file_type="docx",
            suspected_scanned=False,
            blocks=blocks,
            notes=[],
        )

    def _parse_pdf(self, source_path: str) -> ParsedDocumentResult:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("缺少依赖：未安装 pypdf。") from exc

        reader = PdfReader(source_path)
        blocks: list[ParsedBlock] = []
        notes: list[str] = []
        total_text: list[str] = []

        for page_index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                blocks.append(
                    ParsedBlock(
                        block_id=uuid.uuid4().hex,
                        order=len(blocks),
                        page_no=page_index,
                        block_type="text",
                        source="direct",
                        text=page_text,
                        metadata={},
                        layout_hint={},
                    )
                )
                total_text.append(page_text)

            page_images = list(page.images)
            if page_text:
                for image_index, image in enumerate(page_images):
                    blocks.append(
                        ParsedBlock(
                            block_id=uuid.uuid4().hex,
                            order=len(blocks),
                            page_no=page_index,
                            block_type="image",
                            source="direct",
                            text=None,
                            metadata={
                                "image_index": image_index,
                                "image_name": image.name,
                                "image_media_type": self._guess_image_media_type(image.name),
                                "image_bytes": image.data.hex(),
                            },
                            layout_hint={},
                        )
                    )
            else:
                # 对无正文页面统一保留页级渲染入口，后续 OCR 只处理这类稳定输入。
                blocks.append(
                    ParsedBlock(
                        block_id=uuid.uuid4().hex,
                        order=len(blocks),
                        page_no=page_index,
                        block_type="image",
                        source="direct",
                        text=None,
                        metadata={
                            "pdf_page_render": True,
                            "embedded_image_count": len(page_images),
                        },
                        layout_hint={},
                    )
                )

            blocks.append(
                ParsedBlock(
                    block_id=uuid.uuid4().hex,
                    order=len(blocks),
                    page_no=page_index,
                    block_type="page_break",
                    source="direct",
                    text=None,
                    metadata={},
                    layout_hint={},
                )
            )

        raw_text = "\n".join(total_text)
        non_whitespace_chars = len(re.sub(r"\s+", "", raw_text))
        suspected_scanned = non_whitespace_chars < 80
        if suspected_scanned:
            notes.append("直接提取文本过短，文档疑似扫描件，将在 OCR 阶段继续处理。")

        return ParsedDocumentResult(
            parser_status="parsed",
            source_path=source_path,
            file_type="pdf",
            suspected_scanned=suspected_scanned,
            blocks=blocks,
            notes=notes,
        )

    def _guess_image_media_type(self, image_name: str | None) -> str | None:
        if not image_name:
            return None

        suffix = Path(image_name).suffix.lower()
        if suffix in _CUSTOM_IMAGE_MEDIA_TYPES:
            return _CUSTOM_IMAGE_MEDIA_TYPES[suffix]

        guessed_type, _ = mimetypes.guess_type(image_name)
        return guessed_type
