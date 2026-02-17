-- Data loading script (psql)
--
-- Run from the repo root on stearns:
--   psql -d YOUR_DB_NAME -f Data/schema.sql
--   psql -d YOUR_DB_NAME -f Data/load_data.sql

\copy forest_change(entity, code, year, forest_change_ha)
  FROM 'Data/annual-change-forest-area.csv'
  WITH (FORMAT csv, HEADER true);

\copy co2_per_capita(entity, year, co2_tonnes_per_capita)
  FROM 'Data/co-emissions-per-capita.csv'
  WITH (FORMAT csv, HEADER true);

-- Countries are defined as rows with 3-letter uppercase ISO codes
INSERT INTO countries(entity, code)
SELECT DISTINCT entity, code
FROM forest_change
WHERE code ~ '^[A-Z]{3}$'
ON CONFLICT (entity) DO NOTHING;
