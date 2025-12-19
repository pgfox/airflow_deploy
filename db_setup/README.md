# Database Setup Scripts

This directory organizes Postgres bootstrap scripts so you can reproduce the cluster and database structure in a predictable order.

```
db_setup/
  00_cluster/
    001_create_roles.sql
    010_create_extensions.sql
  my_db_1/
    00_database.sql
    10_schemas.sql
    raw/
      001_tables.sql
      010_indexes.sql
    stage/
      001_tables.sql
```

## Execution order

1. Run files under `00_cluster/` against the maintenance database (`postgres`). These create shared roles and extensions.
2. Run `my_db_1/00_database.sql` against `postgres` to create the application database.
3. Connect to `my_db_1` and execute `10_schemas.sql`.
4. Still connected to `my_db_1`, run the schema-specific subdirectories (`raw`, `stage`) in numeric order.

You can run the scripts manually with `psql`:

```bash
psql postgresql://airflow:airflow@localhost:5433/postgres -f db_setup/00_cluster/001_create_roles.sql
psql postgresql://airflow:airflow@localhost:5433/postgres -f db_setup/my_db_1/00_database.sql
psql postgresql://airflow:airflow@localhost:5433/my_db_1 -f db_setup/my_db_1/10_schemas.sql
```

### Automated runner container

This directory also provides a helper compose stack that runs the scripts against the existing `postgres_db` container:

```bash
cd db_setup
docker compose up --build db-setup
```

The service joins `shared_infra_net` and uses the credentials defined in `docker-compose.yaml` (defaults to `airflow/airflow`). Override the environment variables if you need different settings.

Adjust connection strings and credentials as needed. Add new databases or schemas by following the same folder pattern.
