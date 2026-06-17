from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_policy_ingestion_scan(tmp_path: Path) -> None:
    (tmp_path / "资产评估--报告审核制度.docx").write_bytes(b"docx-placeholder")
    (tmp_path / "保密承诺 - 模板.docx").write_bytes(b"template")
    (tmp_path / "旧制度.doc").write_bytes(b"legacy")
    (tmp_path / "盖章版.pdf").write_bytes(b"pdf-placeholder")

    response = client.post(
        "/api/v1/kb/policy-ingestion/scan",
        json={"source_root": str(tmp_path), "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stats"]["total_files"] == 4
    assert payload["stats"]["by_extension"][".docx"] == 2

    by_name = {item["file_name"]: item for item in payload["candidates"]}
    assert by_name["资产评估--报告审核制度.docx"]["recommended_action"] == "include"
    assert by_name["保密承诺 - 模板.docx"]["recommended_action"] == "exclude"
    assert by_name["旧制度.doc"]["recommended_action"] == "review"
    assert by_name["盖章版.pdf"]["parse_method"] == "skip"


def test_policy_ingestion_preview_txt(tmp_path: Path) -> None:
    sample = tmp_path / "信息安全及保密制度.txt"
    sample.write_text(
        "信息安全及保密制度\n\n第一章 总则\n第一条 为了加强信息安全管理。\n第二条 员工离职后仍应承担保密义务。\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/v1/kb/policy-ingestion/preview",
        json={"source_path": str(sample)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parser_status"] == "parsed"
    assert payload["parse_method"] == "direct"
    assert payload["clean_text_chars"] > 0
    assert "第一章 总则" in payload["detected_titles"]
    assert "员工离职后仍应承担保密义务" in payload["text_preview"]
