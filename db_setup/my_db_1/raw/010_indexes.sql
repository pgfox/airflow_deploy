-- Example index definitions; run after creating tables.
CREATE INDEX IF NOT EXISTS idx_ingest_queue_received_at
    ON raw.ingest_queue (received_at DESC);
