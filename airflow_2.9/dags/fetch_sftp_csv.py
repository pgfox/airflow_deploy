from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.sftp.hooks.sftp import SFTPHook

REMOTE_DIR = os.environ.get("SFTP_REMOTE_DIR", "/upload")
LOCAL_BASE = "/opt/airflow/data"
SFTP_CONN_ID = os.environ.get("SFTP_CONN_ID", "sftp_default")


def download_csv_files(**context):
    """Fetch all CSV files from the remote SFTP directory into the shared data volume."""
    hook = SFTPHook(ftp_conn_id=SFTP_CONN_ID)
    os.makedirs(LOCAL_BASE, exist_ok=True)

    # Normalize remote path for joins
    remote_dir = REMOTE_DIR.rstrip("/")
    entries = hook.list_directory(remote_dir)

    for entry in entries:
        if entry in {".", ".."}:
            continue
        if not entry.lower().endswith(".csv"):
            continue

        remote_path = f"{remote_dir}/{entry}"
        local_path = os.path.join(LOCAL_BASE, entry)
        hook.retrieve_file(remote_full_path=remote_path, local_full_path=local_path)


with DAG(
    dag_id="fetch_sftp_csv",
    description="Download CSV files from sftp_con into the shared data volume.",
    schedule_interval=None,  # manual execution
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sftp", "ingest"],
) as dag:
    PythonOperator(
        task_id="download_csv",
        python_callable=download_csv_files,
    )
