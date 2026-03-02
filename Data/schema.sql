-- Schema
-- Tables:
-- forest_change - annual change in forest area (ha)
-- co2_per_capita - annual CO2 emissions per capita (t/person)
-- countries - list of entities treated as countries

DROP TABLE IF EXISTS forest_change;
DROP TABLE IF EXISTS co2_per_capita;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    entity TEXT PRIMARY KEY,
    code   TEXT NOT NULL
);

CREATE TABLE forest_change (
    entity           TEXT NOT NULL,
    code             TEXT,
    year             INTEGER NOT NULL,
    forest_change_ha DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (entity, year)
);

CREATE TABLE co2_per_capita (
    entity               TEXT NOT NULL,
    year                 INTEGER NOT NULL,
    co2_tonnes_per_capita DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (entity, year)
);

CREATE INDEX idx_forest_change_year ON forest_change(year);
CREATE INDEX idx_forest_change_year_value ON forest_change(year, forest_change_ha);
CREATE INDEX idx_co2_year ON co2_per_capita(year);
CREATE INDEX idx_co2_year_value ON co2_per_capita(year, co2_tonnes_per_capita);
