# Airflow 2.9 LocalExecutor Stack

Minimal Apache Airflow 2.9 deployment that connects to the shared `postgres_db` container defined in `postgres/docker-compose.yaml`. The stack runs only Airflow services and relies on the pre-existing `shared_infra_net` network plus the external Postgres instance.

## Prerequisites

- `docker` + Compose plugin
- The `postgres` stack is running and exposes the container on `shared_infra_net` with alias `postgres-db`
- The external network exists (create once via `docker network create shared_infra_net` if needed)

## Layout

- `docker-compose.yaml` – defines webserver + scheduler using `LocalExecutor`
- `dags/`, `logs/`, `plugins/` – bind-mounted into the containers
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
- Because the database lives outside this stack, shut down Airflow with `docker compose down` without affecting the main Postgres container.
- `dags/sample_dag.py` contains a trivial DAG you can enable to verify the deployment.
