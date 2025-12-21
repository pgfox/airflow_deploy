from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.sftp.hooks.sftp import SFTPHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

REMOTE_DIR = os.environ.get("SFTP_REMOTE_DIR", "/home/ubuntu/upload")
LOCAL_BASE = "/opt/airflow/data/sftp_downloads"
SFTP_CONN_ID = os.environ.get("SFTP_CONN_ID", "sftp_default")
POSTGRES_CONN_ID = os.environ.get("POSTGRES_CONN_ID", "airflow_db")
TARGET_TABLE = "raw.orders"


def load_csv_to_postgres(path: str) -> None:
    """Load a CSV file into raw.orders using COPY."""
    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    copy_sql = f"""
    COPY {TARGET_TABLE} (
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
    pg_hook.copy_expert(sql=copy_sql, filename=path)


def download_csv_files(**context):
    """Fetch CSV files from SFTP, store locally, then load into Postgres raw.orders."""
    sftp_hook = SFTPHook(ftp_conn_id=SFTP_CONN_ID)
    os.makedirs(LOCAL_BASE, exist_ok=True)

    remote_dir = REMOTE_DIR.rstrip("/")
    entries = sftp_hook.list_directory(remote_dir)

    for entry in entries:
        if entry in {".", ".."}:
            continue
        if not entry.lower().endswith(".csv"):
            continue

        remote_path = f"{remote_dir}/{entry}"
        local_path = os.path.join(LOCAL_BASE, entry)
        sftp_hook.retrieve_file(remote_full_path=remote_path, local_full_path=local_path)
        load_csv_to_postgres(local_path)


with DAG(
    dag_id="fetch_sftp_csv",
    description="Download CSV files from sftp_con and load them into raw.orders.",
    schedule_interval=None,  # manual execution
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sftp", "ingest"],
) as dag:
    PythonOperator(
        task_id="download_csv",
        python_callable=download_csv_files,
    )
