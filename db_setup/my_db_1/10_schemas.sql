-- Create logical schemas once connected to my_db_1.
CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION airflow_app;
CREATE SCHEMA IF NOT EXISTS stage AUTHORIZATION airflow_app;
