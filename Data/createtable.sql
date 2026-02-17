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

DROP TABLE IF EXISTS temps;
CREATE TABLE temps (
    entity TEXT,
    code TEXT,
    year INTEGER,
    Relative_To_1861_1890 REAL,
    Lower_Bound DOUBLE PRECISION,
    Upper_Bound DOUBLE PRECISION
);

DROP TABLE IF EXISTS forest_change;
CREATE TABLE forest_change (
    entity TEXT,
    code TEXT,
    year INTEGER,
    Annual_Forest_Change DOUBLE PRECISION
);