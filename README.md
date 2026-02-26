# Team Project D – Climate Data Explorer

Group D Team Members: Milly, Simon, Amery

This repo contains:

- `command_line.py` – a command-line interface for querying climate datasets
- `flask_app.py` – a Flask web app with a user-facing website and a JSON API
- `ProductionCode/` – the repository + helpers used by both the CLI and Flask app
- `Tests/` – unit + integration tests for production code, CLI, and Flask routes

The app queries a PostgreSQL database on stearns via the `records` library.

## Setup

Install dependencies:

```bash
python3 -m pip install flask records psycopg2
```

### Database setup on stearns

The database contains 3 tables:

- `forest_change` (annual change in forest area, stored as hectares)
- `co2_per_capita` (annual CO₂ emissions per capita)
- `countries` (the list of entities we treat as countries)

Expected schema is provided in `Data/schema.sql`.

## Command Line Interface

Run help:

```bash
python3 command_line.py -h
```

Supported CLI features (3 independent features):

1. Deforestation / forest change lookup (`--deforestation`)
2. CO₂ per-capita lookup (`--co2`)
3. Forest change ranking (`--ranking`)

Examples:

```bash
python3 command_line.py --deforestation Brazil --year 2020
python3 command_line.py --co2 Canada --year 2021
python3 command_line.py --ranking Brazil --year 2021 --order loss
python3 command_line.py --ranking --year 2021 --order gain --top 10
```

Results are restricted to countries only.


## Flask App

Run the Flask app:

```bash
python3 flask_app.py
```

Then open the URL printed in the terminal.

### Website routes (HTML)

- `/` – homepage with feature forms + example links
- `/deforestation` – forest change value lookup (or top list)
- `/co2` – CO₂ per-capita value lookup (or top list)
- `/ranking` – forest change ranking for a country (or top list)
- `/about` – usage notes

Each feature page supports both:

- Single value / single rank: provide a country (`entity`) and optional `year`
- Top list: leave `entity` blank and use `year`, `top`, and `order` (where applicable)

### API routes (JSON)

All JSON endpoints are available under `/api`, for example:

- `/api/deforestation/United_States?year=2021`
- `/api/co2?year=2021&top=3`
- `/api/ranking/Brazil?year=2021&order=loss`

### Website design: scanning, satisficing, muddling through

- Scanning
  - Clear page headings and short “lead” descriptions.
  - Consistent navigation bar on every page.
  - Tables for ranked lists (easy to skim).

- Satisficing
  - Sensible defaults:
    - omit `year` → uses the latest available year
    - omit `top` → defaults to 10
  - Example links on the homepage and 404 page.

- Muddling through
  - Multiple pathways to information:
    - homepage forms
    - nav bar links
    - direct URLs
  - Helpful 404 page that points to working examples.

### Accessibility

- Skip link (“Skip to main content”)
- `<label for="...">` + matching `id="..."` on form controls
- Semantic headings (`h1`/`h2`) and structured content (`dl`, `table`)
- Responsive layout and relative font sizing (works at 150–200% zoom)


## Running tests

From the repo root:

```bash
python3 -m unittest discover -s Tests -v
```

Coverage:

```bash
python3 -m pip install coverage
python3 -m coverage run --source ProductionCode,flask_app,command_line -m unittest discover -s Tests
python3 -m coverage report -m
```
