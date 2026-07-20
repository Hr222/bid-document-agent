from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for source_path in path.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
    return modules


def test_ingestion_and_knowledge_do_not_depend_on_online_module() -> None:
    assert not any(
        module.startswith("app.modules.online")
        for module in _imported_modules(APP_ROOT / "modules" / "ingestion")
    )
    assert not any(
        module.startswith("app.modules.online")
        for module in _imported_modules(APP_ROOT / "modules" / "knowledge")
    )


def test_online_domain_does_not_depend_on_external_adapters() -> None:
    imported = _imported_modules(APP_ROOT / "modules" / "online" / "domain")
    forbidden_prefixes = (
        "app.infrastructure",
        "app.interfaces",
        "app.modules.knowledge",
        "app.modules.online.contracts",
        "langchain",
        "langgraph",
    )
    assert not any(
        module.startswith(forbidden)
        for module in imported
        for forbidden in forbidden_prefixes
    )


def test_http_schemas_do_not_reuse_ingestion_contracts() -> None:
    imported = _imported_modules(APP_ROOT / "interfaces" / "http" / "schemas")

    assert not any(
        module.startswith("app.modules.ingestion.contracts")
        for module in imported
    )


def test_http_ingestion_routes_use_application_use_cases() -> None:
    route_imports = _imported_modules(APP_ROOT / "interfaces" / "http" / "routes")

    assert "app.modules.ingestion.application.ingestion_use_case" in route_imports
    assert "app.interfaces.http.assemblers.policy_pipeline" in route_imports
    assert "app.interfaces.http.assemblers.policy_ingestion" in route_imports
    assert "app.interfaces.http.assemblers.publication" in route_imports
    assert not any(
        module.startswith("app.modules.ingestion.pipeline")
        for module in route_imports
    )


def test_targeted_architecture_packages_exist_and_old_packages_are_gone() -> None:
    expected_paths = (
        APP_ROOT / "modules" / "ingestion" / "domain",
        APP_ROOT / "modules" / "ingestion" / "ports",
        APP_ROOT / "modules" / "knowledge" / "domain",
        APP_ROOT / "modules" / "knowledge" / "ports",
        APP_ROOT / "modules" / "online" / "domain" / "checklist",
        APP_ROOT / "interfaces" / "agent" / "contracts.py",
        APP_ROOT / "infrastructure" / "filesystem",
        APP_ROOT / "infrastructure" / "ocr",
        APP_ROOT / "composition" / "online.py",
        APP_ROOT / "composition" / "knowledge.py",
        APP_ROOT / "composition" / "ingestion.py",
    )
    assert all(path.exists() for path in expected_paths)

    old_paths = (
        APP_ROOT / "api",
        APP_ROOT / "application",
        APP_ROOT / "bridges",
        APP_ROOT / "core",
        APP_ROOT / "db",
        APP_ROOT / "domain",
        APP_ROOT / "models",
        APP_ROOT / "repositories",
        APP_ROOT / "schemas",
        APP_ROOT / "services",
    )
    assert all(not path.exists() for path in old_paths)


def test_online_decision_is_composed_from_knowledge_query_capability() -> None:
    root_source = (APP_ROOT / "composition" / "root.py").read_text(encoding="utf-8")
    assert (
        "build_rule_retrieval_service(\n                self.knowledge_query_capability()"
        in root_source
    )
    assert (
        "build_decision_service(\n                self.knowledge_query_capability()"
        in root_source
    )


def test_sensitive_ocr_outputs_are_not_kept_in_tests() -> None:
    assert not (PROJECT_ROOT / "tests" / "ocr").exists()
    assert not (PROJECT_ROOT / "tests" / "ocr" / "output").exists()

    classifier_source = (PROJECT_ROOT / "tools" / "ocr" / "classify_sample_inventory.py").read_text(
        encoding="utf-8"
    )
    ocr_source = (PROJECT_ROOT / "tools" / "ocr" / "tencent_ocr_mvp.py").read_text(
        encoding="utf-8"
    )
    assert "tests/ocr/output" not in classifier_source
    assert "tests/ocr/output" not in ocr_source
