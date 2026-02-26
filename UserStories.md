# User Stories (Command Line Component)

User stories supported by `command_line.py`,
points to the acceptance tests in `Tests/test_command_line.py`.

## User Story 1: Forest change (deforestation proxy) value lookup

As a user, I want to know the annual change in forest area for a specific
country in a specific year, so that I can understand forest loss or gain.

- CLI feature: `--deforestation COUNTRY`
- Optional arguments:
  - `--year YEAR` (if omitted, default to the latest year available for that country)

Acceptance tests:
- `TestCommandLine.test_deforestation_single_value`
- `TestCommandLine.test_deforestation_single_value_defaults_to_latest_year`

## User Story 2: CO₂ emissions per capita value lookup

As a user, I want to know the annual CO₂ emissions per capita for a specific
country in a specific year, so that I can compare countries over time.

- CLI feature: `--co2 COUNTRY`
- Optional arguments:
  - `--year YEAR` (if omitted, default to the latest year available for that country)

Acceptance tests:
- `TestCommandLine.test_co2_single_value`
- `TestCommandLine.test_co2_single_value_defaults_to_latest_year`

## User Story 3: Forest change ranking

As a user, I want to see how a country ranks compared to others for forest
change in a given year, so that I can quickly understand whether it is among the
largest losses or gains.

- CLI feature: `--ranking COUNTRY`
- Optional arguments:
  - `--year YEAR` (defaults to the latest year available for that country)
  - `--order loss|gain` (rank by largest losses or largest gains)

Acceptance tests:
- `TestCommandLine.test_ranking_single_value`
- `TestCommandLine.test_ranking_single_value_defaults_to_latest_year`
- `TestCommandLine.test_ranking_list`


# User Stories (Flask Component)

The Flask app (`flask_app.py`) supports the same user stories as the CLI.

## User Story 1 (Web): Forest change value + list

- Single value: `/deforestation/<country>?year=YYYY`
- List output: `/deforestation?year=YYYY&top=N&order=loss|gain`

## User Story 2 (Web): CO₂ per-capita value + list

- Single value: `/co2/<country>?year=YYYY`
- List output: `/co2?year=YYYY&top=N`

## User Story 3 (Web): Forest change ranking

- Single country rank: `/ranking/<country>?year=YYYY&order=loss|gain`
- List output: `/ranking?year=YYYY&top=N&order=loss|gain`


# User Stories (Website Component)

These same three user stories are supported in the Flask website (`flask_app.py`).
Users can reach the feature pages using the homepage forms or the navigation bar.

## Web User Story 1: Forest change value lookup

As a user, I want to look up the annual change in forest area for a country in a year,
so that I can understand forest loss or gain.

- Website route: `/deforestation`
- Inputs (HTML form / query params): `entity`, optional `year`

Acceptance tests:
- `TestFlaskHtmlRoutes.test_deforestation_value`
- `TestFlaskHtmlRoutes.test_deforestation_list_uses_latest_year_when_missing`

## Web User Story 2: CO₂ per-capita value lookup

As a user, I want to look up annual CO₂ emissions per capita for a country in a year,
so that I can compare countries over time.

- Website route: `/co2`
- Inputs: `entity`, optional `year`

Acceptance tests:
- `TestFlaskHtmlRoutes.test_co2_value`
- `TestFlaskHtmlRoutes.test_co2_list_uses_latest_year_when_missing`

## Web User Story 3: Forest change ranking

As a user, I want to see a country’s ranking for forest change (loss or gain) in a year,
so that I can quickly compare it to others.

- Website route: `/ranking`
- Inputs: `entity` (or leave blank for a list), optional `year`, `order`

Acceptance tests:
- `TestFlaskHtmlRoutes.test_ranking_value`
- `TestFlaskHtmlRoutes.test_ranking_list_route_renders`
