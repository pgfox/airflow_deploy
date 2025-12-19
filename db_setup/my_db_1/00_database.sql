-- Create the application database. Run against the postgres maintenance DB.
SELECT 'CREATE DATABASE my_db_1 OWNER airflow_app'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'my_db_1'
)\gexec
