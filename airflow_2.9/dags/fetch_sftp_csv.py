from __future__ import annotations

import os
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.sftp.hooks.sftp import SFTPHook

# Configuration
REMOTE_DIR = os.environ.get("SFTP_REMOTE_DIR", "upload")
LOCAL_BASE = Path("/opt/airflow/data/landing")
SFTP_CONN_ID = os.environ.get("SFTP_CONN_ID", "sftp_default")
POSTGRES_CONN_ID = os.environ.get("POSTGRES_CONN_ID", "postgres_db")
BATCH_TABLE = "metadata.batches"
RAW_TABLE = "raw.orders"
CLEAN_TABLE = "stage.orders_clean"
QUAR_TABLE = "dq.quarantine_orders"
ALLOWED_SUFFIX = ".csv"


def _get_pg_hook() -> PostgresHook:
    return PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)


def discover_sftp_files(**context) -> None:
    """List remote CSVs and register them in metadata.batches as status=new."""
    hook = SFTPHook(ftp_conn_id=SFTP_CONN_ID)
    client = hook.get_conn()
    remote_dir = REMOTE_DIR.rstrip("/")
    entries = hook.list_directory(remote_dir)

    rows = []
    for entry in entries:
        if entry in {".", ".."}:
            continue
        name = entry.lower()
        if not (name.startswith("order_") and name.endswith(ALLOWED_SUFFIX)):
            continue
        remote_path = f"{remote_dir}/{entry}"
        stat = client.stat(remote_path)
        rows.append(
            {
                "remote_path": remote_path,
                "file_name": entry,
                "file_size": stat.st_size,
                "file_mtime": datetime.fromtimestamp(stat.st_mtime),
            }
        )

    if not rows:
        return

    insert_sql = f"""
    INSERT INTO {BATCH_TABLE} (remote_path, file_name, file_size, file_mtime, status)
    VALUES (%(remote_path)s, %(file_name)s, %(file_size)s, %(file_mtime)s, 'new')
    ON CONFLICT (remote_path) DO NOTHING;
    """
    pg_hook = _get_pg_hook()
    conn = pg_hook.get_conn()
    with conn, conn.cursor() as cur:
        cur.executemany(insert_sql, rows)
    conn.commit()


def claim_batch(**context) -> Dict[str, str]:
    """Atomically claim one new batch using SKIP LOCKED."""
    pg_hook = _get_pg_hook()
    hostname = socket.gethostname()
    dag_id = context["dag"].dag_id
    run_id = context["run_id"]

    sql = f"""
    WITH c AS (
        SELECT batch_id
        FROM {BATCH_TABLE}
        WHERE status = 'new'
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    UPDATE {BATCH_TABLE} b
    SET status = 'ingesting',
        claimed_at = now(),
        claimed_by = %s,
        attempt = COALESCE(attempt, 0) + 1,
        dag_id = %s,
        run_id = %s
    FROM c
    WHERE b.batch_id = c.batch_id
    RETURNING b.batch_id, b.remote_path, b.file_name;
    """
    conn = pg_hook.get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(sql, (hostname, dag_id, run_id))
        row = cur.fetchone()
        conn.commit()

    if not row:
        raise AirflowSkipException("No batches available to claim.")

    batch_id, remote_path, file_name = row
    return {
        "batch_id": batch_id,
        "remote_path": remote_path,
        "file_name": file_name,
    }


def download_claimed_batch(ti, **context) -> Dict[str, str]:
    """Download the claimed file to the landing directory and persist local_path."""
    batch = ti.xcom_pull(task_ids="claim_batch")
    if not batch:
        raise AirflowSkipException("No batch claimed; skipping download.")

    LOCAL_BASE.mkdir(parents=True, exist_ok=True)
    local_path = LOCAL_BASE / f"{batch['batch_id']}__{batch['file_name']}"

    sftp_hook = SFTPHook(ftp_conn_id=SFTP_CONN_ID)
    sftp_hook.retrieve_file(batch["remote_path"], str(local_path))

    pg_hook = _get_pg_hook()
    update_sql = f"""
    UPDATE {BATCH_TABLE}
    SET local_path = %s
    WHERE batch_id = %s
    """
    pg_hook.run(update_sql, parameters=(str(local_path), batch["batch_id"]))

    batch["local_path"] = str(local_path)
    return batch


def load_to_postgres(ti, **context) -> Dict[str, str]:
    """Load the downloaded CSV into a staging table using COPY."""
    batch = ti.xcom_pull(task_ids="download_claimed_batch")
    if not batch or "local_path" not in batch:
        raise AirflowSkipException("No local file found for load.")

    pg_hook = _get_pg_hook()
    ddl = f"""
    CREATE SCHEMA IF NOT EXISTS raw;
    CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
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
    """
    pg_hook.run(ddl)
    pg_hook.run(f"TRUNCATE TABLE {RAW_TABLE};")

    copy_sql = f"""
    COPY {RAW_TABLE} (
        customer_name,
        address,
        product_name,
        product_id,
        quantity,
        purchase_date,
        invoice_id,
        product_cost
    )
    FROM STDIN WITH CSV HEADER
    """
    pg_hook.copy_expert(sql=copy_sql, filename=batch["local_path"])
    pg_hook.run(f"UPDATE {RAW_TABLE} SET batch_id = %s", parameters=(batch["batch_id"],))

    return batch


def mark_ingested(ti, **context) -> None:
    batch = ti.xcom_pull(task_ids="load_to_postgres")
    if not batch:
        raise AirflowSkipException("No batch to mark ingested.")
    pg_hook = _get_pg_hook()
    pg_hook.run(
        f"UPDATE {BATCH_TABLE} SET status='ingested', ingested_at=now() WHERE batch_id = %s",
        parameters=(batch["batch_id"],),
    )

def dq_batch(ti, **context) -> None:
    """DQ split: good rows to stage.orders_clean, bad rows to dq.quarantine_orders."""
    batch = ti.xcom_pull(task_ids="load_to_postgres")
    if not batch:
        raise AirflowSkipException("No batch to DQ.")
    
    batch_id = batch["batch_id"]

    condition = """
        quantity IS NOT NULL AND quantity > 1 AND quantity < 1000
        AND customer_name IS NOT NULL AND btrim(customer_name) <> ''
        AND address IS NOT NULL AND btrim(address) <> ''
        AND product_id IS NOT NULL AND btrim(product_id) <> ''
        AND purchase_date IS NOT NULL AND purchase_date >= DATE '2024-01-01'
        AND product_cost IS NOT NULL AND product_cost > 0
    """

    pg_hook = _get_pg_hook()
    ddl = f"""
    CREATE SCHEMA IF NOT EXISTS stage;
    CREATE SCHEMA IF NOT EXISTS dq;
    CREATE TABLE IF NOT EXISTS {CLEAN_TABLE} (LIKE {RAW_TABLE} INCLUDING ALL);
    CREATE TABLE IF NOT EXISTS {QUAR_TABLE} (
        batch_id BIGINT,
        payload JSONB,
        error_code TEXT,
        error_detail TEXT,
        dag_id TEXT,
        run_id TEXT,
        quarantined_at TIMESTAMPTZ DEFAULT now()
    );
    """
    pg_hook.run(ddl)

    # Clear any previous rows for this batch
    pg_hook.run(f"DELETE FROM {CLEAN_TABLE} WHERE batch_id = %s", parameters=(batch_id,))
    pg_hook.run(f"DELETE FROM {QUAR_TABLE} WHERE batch_id = %s", parameters=(batch_id,))

    pg_hook.run(
        f"""
        INSERT INTO {CLEAN_TABLE}
        SELECT *
        FROM {RAW_TABLE}
        WHERE batch_id = %s AND {condition}
        """,
        parameters=(batch_id,),
    )

    pg_hook.run(
        f"""
        INSERT INTO {QUAR_TABLE} (batch_id, payload, error_code, error_detail, dag_id, run_id)
        SELECT
            %s,
            to_jsonb(r.*),
            'DQ_VALIDATION_FAILED',
            'Failed validation rules',
            %s,
            %s
        FROM {RAW_TABLE} r
        WHERE batch_id = %s AND NOT ({condition})
        """,
        parameters=(batch_id, context["dag"].dag_id, context["run_id"], batch_id),
    )



def process_batch(ti, **context) -> None:
    """Placeholder transform/DQ step; marks batch done."""
    batch = ti.xcom_pull(task_ids="load_to_postgres")
    if not batch:
        raise AirflowSkipException("No batch to process.")
    pg_hook = _get_pg_hook()
    pg_hook.run(
        f"UPDATE {BATCH_TABLE} SET status='done', completed_at=now() WHERE batch_id = %s",
        parameters=(batch["batch_id"],),
    )


with DAG(
    dag_id="fetch_sftp_csv",
    description="Discover, claim, download, and load exactly one SFTP CSV batch per run.",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sftp", "ingest"],
) as dag:
    discover = PythonOperator(
        task_id="discover_sftp_files",
        python_callable=discover_sftp_files,
    )

    claim = PythonOperator(
        task_id="claim_batch",
        python_callable=claim_batch,
    )

    download = PythonOperator(
        task_id="download_claimed_batch",
        python_callable=download_claimed_batch,
    )

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres,
    )

    mark = PythonOperator(
        task_id="mark_ingested",
        python_callable=mark_ingested,
    )

    dq = PythonOperator(
        task_id="dq_batch",
        python_callable=dq_batch,
    )

    process = PythonOperator(
        task_id="process_batch",
        python_callable=process_batch,
    )

    discover >> claim >> download >> load >> mark >> dq >> process 
