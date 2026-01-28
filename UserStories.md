# User Stories (Command Line Component)

This file lists the user stories supported by `command_line.py` and points to the
acceptance tests in `Tests/test_command_line.py`.

## User Story 1: Forest change (deforestation proxy) value lookup

**As a user**, I want to know the annual change in forest area for a specific
country in a specific year, so that I can understand forest loss or gain.

- CLI feature: `--deforestation COUNTRY`
- Optional arguments:
  - `--year YEAR` (if omitted, default to the latest year available for that country)
  - `--include-aggregates` (include regions/aggregates instead of only countries)
  - `--data-dir PATH` (custom data directory)

Acceptance tests:
- `TestCommandLineAcceptance.test_cli_deforestation_value`
- `TestCommandLineAcceptance.test_cli_deforestation_default_year`

## User Story 2: CO₂ emissions per capita value lookup

**As a user**, I want to know the annual CO₂ emissions per capita for a specific
country in a specific year, so that I can compare countries over time.

- CLI feature: `--co2 COUNTRY`
- Optional arguments:
  - `--year YEAR` (if omitted, default to the latest year available for that country)
  - `--include-aggregates` (include regions/aggregates instead of only countries)
  - `--data-dir PATH` (custom data directory)

Acceptance tests:
- `TestCommandLineAcceptance.test_cli_co2_value`
- `TestCommandLineAcceptance.test_cli_co2_default_year`

## User Story 3: Forest change ranking

**As a user**, I want to see how a country ranks compared to others for forest
change in a given year, so that I can quickly understand whether it is among the
largest losses or gains.

- CLI feature: `--ranking COUNTRY`
- Optional arguments:
  - `--year YEAR` (defaults to the latest year available for that country)
  - `--order loss|gain` (rank by largest losses or largest gains)
  - `--include-aggregates` (include regions/aggregates instead of only countries)
  - `--data-dir PATH` (custom data directory)

Acceptance tests:
- `TestCommandLineAcceptance.test_cli_ranking_for_country`
- `TestCommandLineAcceptance.test_cli_list_outputs` (lists top entries when no country is provided)
