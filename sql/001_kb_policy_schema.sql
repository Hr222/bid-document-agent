-- Knowledge base schema for policy documents
-- Phase 1: 管理制度 / 版本化 / 审核留痕 / 检索切块

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS kb_policy_document (
    id BIGSERIAL PRIMARY KEY,
    policy_code TEXT UNIQUE,
    policy_name TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    department_owner TEXT,
    current_version_id BIGINT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_policy_version (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    version_seq INTEGER NOT NULL,
    version_label TEXT,
    source_year INTEGER,
    source_document_date DATE,
    issued_at DATE,
    effective_date DATE,
    expired_at DATE,
    supersedes_version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    revision_type TEXT NOT NULL DEFAULT 'revise',
    change_summary TEXT,
    change_reason TEXT,
    source_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_ext TEXT,
    file_hash TEXT,
    is_scanned BOOLEAN NOT NULL DEFAULT FALSE,
    parse_method TEXT NOT NULL DEFAULT 'direct',
    raw_text TEXT,
    clean_text TEXT,
    page_count INTEGER,
    parser_status TEXT NOT NULL DEFAULT 'pending',
    version_status TEXT NOT NULL DEFAULT 'draft',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_version UNIQUE (policy_id, version_seq)
);

CREATE TABLE IF NOT EXISTS kb_policy_section (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    parent_section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE CASCADE,
    section_no TEXT,
    section_title TEXT,
    section_order INTEGER NOT NULL DEFAULT 0,
    page_start INTEGER,
    page_end INTEGER,
    section_text TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'pending',
    review_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_policy_chunk (
    id BIGSERIAL PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    section_id BIGINT REFERENCES kb_policy_section(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL,
    page_no INTEGER,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kb_policy_chunk UNIQUE (version_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS kb_policy_review_record (
    id BIGSERIAL PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id BIGINT NOT NULL,
    version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    review_action TEXT NOT NULL,
    review_comment TEXT,
    reviewer TEXT,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_policy_version_change (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    from_version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    to_version_id BIGINT NOT NULL REFERENCES kb_policy_version(id) ON DELETE CASCADE,
    change_type TEXT NOT NULL,
    change_scope TEXT NOT NULL DEFAULT 'section',
    affected_sections TEXT,
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_policy_profile (
    id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES kb_policy_document(id) ON DELETE CASCADE,
    version_id BIGINT REFERENCES kb_policy_version(id) ON DELETE SET NULL,
    policy_type TEXT NOT NULL,
    applicable_scope TEXT,
    department_owner TEXT,
    approval_level TEXT,
    keywords TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_policy_document_status ON kb_policy_document(status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_document_type ON kb_policy_document(policy_type);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_policy_id ON kb_policy_version(policy_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_status ON kb_policy_version(version_status);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_effective_date ON kb_policy_version(effective_date);
CREATE INDEX IF NOT EXISTS idx_kb_policy_section_version_id ON kb_policy_section(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_chunk_version_id ON kb_policy_chunk(version_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_review_record_target ON kb_policy_review_record(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_kb_policy_version_change_policy_id ON kb_policy_version_change(policy_id);
