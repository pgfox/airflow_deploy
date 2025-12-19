-- Create shared roles used across databases in this cluster.
-- Run against the postgres maintenance DB (usually "postgres").
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow_app') THEN
      CREATE ROLE airflow_app LOGIN PASSWORD 'airflow';
   END IF;

   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'etl_runner') THEN
      CREATE ROLE etl_runner LOGIN PASSWORD 'etl_runner';
   END IF;
END
$$;
