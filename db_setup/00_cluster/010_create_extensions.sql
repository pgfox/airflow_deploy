-- Install extensions that should be available cluster-wide.
-- Execute against the "postgres" database or any admin DB.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
