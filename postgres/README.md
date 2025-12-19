# Standalone PostgreSQL Container

This folder defines a PostgreSQL 15 container that persists its data in a named Docker volume so information survives container recreation.

## Prerequisites

- Docker + Docker Compose plugin
- The shared network `shared_infra_net` already created (see `docker-compose.network.yaml` in repo root)

## Provision the data volume (one time)

A named volume `postgres_data_vol` has been created already via:
```bash
docker volume create postgres_data_vol
```
If you ever need to recreate it manually, run the command above (note: removing the volume deletes all DB data).

## Run PostgreSQL

```bash
cd postgres
# Build not needed because we use the official image
docker compose up -d
```

The service maps host port `5433` to container port `5432` so it does not clash with any other Postgres instances. Default credentials:
- user: `airflow`
- password: `airflow`
- database: `airflow`

Test the connection (requires `psql`):
```bash
psql postgresql://airflow:airflow@localhost:5433/airflow
```

The container joins the `shared_infra_net` network with alias `postgres-db`, allowing other compose stacks in this repo to reference `postgres-db:5432`.

## Lifecycle

- Stop containers: `docker compose down`
- Stop and remove containers but keep data: `docker compose down --remove-orphans`
- Remove containers and the persistent data volume: `docker compose down --volumes` (data loss!)
