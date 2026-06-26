from sqlalchemy.exc import ProgrammingError

from app.db.schema_health import KB_SCHEMA_SETUP_GUIDE, is_missing_kb_schema_error


def test_missing_kb_schema_error_detection_matches_undefined_table_message() -> None:
    exc = ProgrammingError(
        'SELECT * FROM kb_policy_document',
        {},
        Exception('relation "kb_policy_document" does not exist'),
    )

    assert is_missing_kb_schema_error(exc) is True


def test_missing_kb_schema_setup_guide_mentions_sql_scripts() -> None:
    assert "sql/001_kb_policy_schema.sql" in KB_SCHEMA_SETUP_GUIDE
    assert "sql/002_kb_policy_chunk_embedding_dimension_1024.sql" in KB_SCHEMA_SETUP_GUIDE
