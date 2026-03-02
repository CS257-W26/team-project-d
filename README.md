# Team Project D – Climate Data Explorer

Team members: Milly, Simon, Amery

This repository contains a database-driven web app (Flask + PostgreSQL) for exploring two climate indicators by country and year:

- CO₂ emissions per capita (tonnes per person)
- Annual change in forest area (hectares)

The user-facing website front-end design: a homepage form and a single dashboard page that shows both metrics and a year-by-year table.

## Repository structure

- `flask_app.py` – Flask app (website + JSON API)
- `command_line.py` – command-line interface for quick lookups
- `ProductionCode/` – database repository + helper modules
- `templates/` – HTML templates (content/structure only)
- `static/` – CSS styling
- `Tests/` – unit + integration tests
- `Data/schema.sql` – SQL schema for the team database (no CSV files are used)

## Running the website


### On stearns

Create `ProductionCode/psql_config.py` (this file is gitignored):

```python
DATABASE = "teamd"
USER = "teamd"
PASSWORD = "YOUR_TEAM_DB_PASSWORD"
HOST = "localhost"
```

Run the app using a port assigned to you:

```bash
flask --app flask_app:create_app run --host 0.0.0.0 --port YOUR_PORT
```

## Using the website

- Scanning: The dashboard uses clear headings and a two-card summary so you can quickly scan the key numbers for the selected year.
- Satisficing: The homepage defaults to a valid country and the latest year with data; you can get useful results without tuning options.
- Muddling through: The year-by-year table lets you explore trends gradually (try different years/countries and compare).

If you type an incorrect URL, the 404 page includes links and an example dashboard URL to get back on track.

## Running the CLI

Forest change (defaults to latest year for that metric):

```bash
python3 command_line.py --deforestation "United States"
```

Forest change for a specific year:

```bash
python3 command_line.py --deforestation "United States" --year 2010
```

CO₂ per-capita:

```bash
python3 command_line.py --co2 "United States" --year 2010
```

## JSON API

These routes return JSON and accept an optional `year` query parameter:

- `GET /api/deforestation/<country>`
- `GET /api/co2/<country>`
- `GET /api/dashboard/<country>` (uses intersection years where both metrics exist)

Example:

- `/api/dashboard/United_States?year=2010`

## Tests

Run all tests:

```bash
python3 -m unittest discover -s Tests
```

## Dependencies

- `flask` – web framework (routes, templates, request handling)
- `records` – database connection + query execution against PostgreSQL
- `argparse` – parsing command-line arguments
- `unittest` / `unittest.mock` – automated testing and patching
