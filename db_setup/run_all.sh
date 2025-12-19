#!/usr/bin/env bash
set -euo pipefail

: "${PGHOST:=postgres-db}"
: "${PGPORT:=5432}"
: "${PGUSER:=airflow}"
: "${PGPASSWORD:=airflow}"
: "${MAINTENANCE_DB:=postgres}"
: "${APP_DB:=my_db_1}"

export PGPASSWORD

psql_maint() {
  psql "postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${MAINTENANCE_DB}" -v ON_ERROR_STOP=1 "$@"
}

psql_app() {
  psql "postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${APP_DB}" -v ON_ERROR_STOP=1 "$@"
}

echo "Running cluster-level scripts against ${MAINTENANCE_DB}@${PGHOST}:${PGPORT}"
psql_maint -f 00_cluster/001_create_roles.sql
psql_maint -f 00_cluster/010_create_extensions.sql

echo "Creating databases and schemas"
psql_maint -f my_db_1/00_database.sql

echo "Configuring schemas/tables inside ${APP_DB}"
psql_app -f my_db_1/10_schemas.sql
psql_app -f my_db_1/raw/001_tables.sql
psql_app -f my_db_1/raw/010_indexes.sql
psql_app -f my_db_1/stage/001_tables.sql

echo "Database setup complete."
