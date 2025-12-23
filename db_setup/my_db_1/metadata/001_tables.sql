-- Metadata tables for ingestion tracking
CREATE TABLE IF NOT EXISTS metadata.batches (
    batch_id BIGSERIAL PRIMARY KEY,
    remote_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    file_mtime TIMESTAMPTZ,
    local_path TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    attempt INTEGER NOT NULL DEFAULT 0,
    claimed_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    claimed_by TEXT,
    dag_id TEXT,
    run_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
