-- Sample raw schema tables. Connect to my_db_1 before running.
CREATE TABLE IF NOT EXISTS raw.ingest_queue (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
