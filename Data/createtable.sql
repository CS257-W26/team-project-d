DROP TABLE IF EXISTS deforestation_share_forest;
CREATE TABLE deforestation_share_forest (
    entity TEXT,
    country_code TEXT,
    year INTEGER,
    deforestation DOUBLE PRECISION
);

DROP TABLE IF EXISTS co2;
CREATE TABLE co2 (
    entity TEXT,
    year INTEGER,
    co2_per_capita DOUBLE PRECISION
);