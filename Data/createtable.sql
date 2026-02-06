DROP TABLE IF EXISTS deforestation_share_forest;
CREATE TABLE deforestation_share_forest(
  entity TEXT,
  country_code TEXT,
  year YEAR,
  deforestation DOUBLE PRECISION,
);

DROP TABLE IF EXISTS co2_emission_per_capita;
CREATE TABLE co2_emission_per_capita(
    entity TEXT,
    year YEAR,
    co2_per_capita DOUBLE PRECISION,
);