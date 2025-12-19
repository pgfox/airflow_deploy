-- Stage schema tables. Execute after schemas are created.
CREATE TABLE IF NOT EXISTS stage.processed_events (
    id BIGINT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL,
    metadata JSONB
);
