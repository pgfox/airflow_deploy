# Airflow 2.9 LocalExecutor Stack

Minimal Apache Airflow 2.9 deployment that connects to the shared `postgres_db` container defined in `postgres/docker-compose.yaml`. The stack runs only Airflow services and relies on the pre-existing `shared_infra_net` network plus the external Postgres instance.

## Prerequisites

- `docker` + Compose plugin
- The `postgres` stack is running and exposes the container on `shared_infra_net` with alias `postgres-db`
- The external network exists (create once via `docker network create shared_infra_net` if needed)

## Layout

- `docker-compose.yaml` – defines webserver + scheduler using `LocalExecutor`
- `dags/`, `logs/`, `plugins/` – bind-mounted into the containers
- `data_vol` – named Docker volume mounted at `/opt/airflow/data` for temporary SFTP downloads
- `.env` – sets `AIRFLOW_UID/GID` for file permissions

## Usage

```bash
cd airflow_2.9
# Prepare folders (already committed, but harmless if re-run):
mkdir -p dags logs plugins

# Run database migrations and create the default user
docker compose run --rm airflow-init

# Start the webserver + scheduler
docker compose up airflow-webserver airflow-scheduler
```

The Airflow UI listens on http://localhost:8090 with `admin/admin`. Logs and DAGs are stored in the local folders so they persist across container restarts.

## Notes

- Update `docker-compose.yaml` if you want to change the Postgres credentials or host/port.
- The `data_vol` volume holds temporary data fetched from SFTP; remove it with `docker volume rm airflow_2.9_data_vol` when you want a clean slate.
- If you hit permission issues writing to `/opt/airflow/data`, run `docker compose run --rm data-permissions` once to chown the volume to the Airflow user.
- Because the database lives outside this stack, shut down Airflow with `docker compose down` without affecting the main Postgres container.
- `dags/sample_dag.py` contains a trivial DAG you can enable to verify the deployment.
- `dags/fetch_sftp_csv.py` downloads `.csv` files from `sftp_con` into `/opt/airflow/data/sftp_downloads` and loads them into `raw.orders` in Postgres.

### Configure the SFTP connection

The DAG expects an Airflow connection named `sftp_default` that points to the `sftp_con` service. Create it via the UI or CLI:

```bash
docker compose run --rm airflow-webserver \
  airflow connections add sftp_default \
    --conn-uri sftp://ubuntu:ubuntu@sftp-server:22
```

### Configure the Postgres connection

The same DAG uses a Postgres connection named `airflow_db` to write into `raw.orders`. Point it at the shared Postgres backend:

```bash
docker compose run --rm airflow-webserver \
  airflow connections add airflow_db \
    --conn-uri postgresql://airflow:airflow@postgres-db:5432/airflow
```

### Run the `fetch_sftp_csv` DAG manually

```bash
# Trigger once (scheduler/webserver should already be running)
docker compose run --rm airflow-webserver \
  airflow dags trigger fetch_sftp_csv
```

The task copies any `.csv` file from `/home/ubuntu/upload` on the SFTP server into the shared volume under `data/sftp_downloads/` on the host.
