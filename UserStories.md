# User Stories

This file lists the two project features supported by our site and points to the
acceptance tests.

## US1: Country dashboard snapshot

As a user interested in climate and sustainability,
I want to choose a country and year and see both CO₂ per-capita and annual
forest change,
so that I can quickly compare two indicators for the same place and time.

### Acceptance criteria
- Given a valid country and year, when I open
  `/country?entity=<country>&year=<year>`, the page shows:
  - the selected country and year
  - a CO₂ per-capita value
  - a forest-change value
- Given a valid country but no year, the dashboard defaults to the latest year
  where both metrics exist.
- The JSON API supports the same lookup at `/api/dashboard/<country>`.
- The command line supports direct single-metric lookups with:
  - `python3 command_line.py --deforestation "United States" --year 2010`
  - `python3 command_line.py --co2 "United States" --year 2010`

### Acceptance tests
- `Tests/test_flask_app.py`
- `Tests/test_command_line.py`

## US2: Trend scanning table

As a user,
I want to see a year-by-year table for the selected country,
so that I can scan trends over time without leaving the page.

### Acceptance criteria
- The dashboard includes a table with multiple years for the selected country.
- The selected year is visually highlighted in the table.
- Invalid routes show a helpful 404 page with working examples so users can
  recover and keep exploring.

### Acceptance tests
- `Tests/test_flask_app.py`

## CLI user stories

### US3: Forest change lookup
As a user,
I want to query forest change for a country (and optionally a year) from the command line,
so that I can get a quick numeric result.

#### Acceptance criteria
- `python3 command_line.py --deforestation "United States" --year 2010` prints a single value and exits 0.
- If the year is omitted, the CLI defaults to the latest available year for that metric.

#### Acceptance tests
- `Tests/test_command_line.py`

### US4: CO₂ per-capita lookup
As a user,
I want to query CO₂ per-capita for a country (and optionally a year) from the command line,
so that I can get a quick numeric result.

#### Acceptance criteria
- `python3 command_line.py --co2 "United States" --year 2010` prints a single value and exits 0.
- If the year is omitted, the CLI defaults to the latest available year for that metric.

#### Acceptance tests
- `Tests/test_command_line.py`
- `Tests/test_flask_app.py`
