-- Sample raw schema tables. Connect to my_db_1 before running.
CREATE TABLE IF NOT EXISTS raw.ingest_queue (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Orders ingested from SFTP CSV files
CREATE TABLE IF NOT EXISTS raw.orders (
    batch_id BIGINT,
    customer_name TEXT,
    address TEXT,
    product_name TEXT,
    product_id TEXT,
    quantity INTEGER,
    purchase_date DATE,
    invoice_id TEXT,
    product_cost NUMERIC(12,2)
);
