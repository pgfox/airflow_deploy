CREATE INDEX IF NOT EXISTS idx_batches_status_created_at
    ON metadata.batches (status, created_at);
