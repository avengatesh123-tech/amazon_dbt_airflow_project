-- Run this script while connected to the target Neon database as the database owner.
-- Replace the placeholder password before running it. Do not commit the real password.

SELECT current_database();
SHOW wal_level;

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1
		FROM pg_roles
		WHERE rolname = 'databricks_replication'
	) THEN
		CREATE ROLE databricks_replication
			WITH LOGIN REPLICATION PASSWORD 'REPLACE_WITH_A_STRONG_PASSWORD';
	ELSE
		ALTER ROLE databricks_replication
			WITH LOGIN REPLICATION PASSWORD 'REPLACE_WITH_A_STRONG_PASSWORD';
	END IF;
END
$$;

GRANT CONNECT ON DATABASE amazon TO databricks_replication;
GRANT USAGE ON SCHEMA public TO databricks_replication;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO databricks_replication;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
	GRANT SELECT ON TABLES TO databricks_replication;

CREATE PUBLICATION IF NOT EXISTS databricks_publication
	FOR ALL TABLES;

-- Create the slot while connected as the replication role, not with SET ROLE.
-- SELECT pg_create_logical_replication_slot('databricks_slot', 'pgoutput');

SELECT slot_name, slot_type, active
FROM pg_replication_slots
WHERE slot_name = 'databricks_slot';