# Team Project D – Climate Data Explorer

Team members: Milly, Simon, Amery

This repository contains a database-driven web app (Flask + PostgreSQL) for exploring two climate indicators by country and year:

- CO₂ emissions per capita (tonnes per person)
- Annual change in forest area (hectares)

The user-facing website includes a homepage form and a dashboard page that shows both metrics, trend charts, and a year-by-year table.

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

- Scanning: The dashboard uses clear headings, two summary cards, and trend charts so you can quickly scan the key numbers and overall direction for the selected country.
- Satisficing: The homepage defaults to a valid country and the latest year with data; you can get useful results without tuning options.
- Muddling through: The year-by-year table lets you explore trends gradually (try different years and countries and compare).

If you type an incorrect URL, the 404 page includes links and an example dashboard URL to get back on track.

## Accessibility

- Text can be resized to 150–200% without losing content or navigation because the layout uses flexible containers and scalable text sizes.
- Headings structure each page so screen-reader users and sighted users can quickly understand the page hierarchy.
- The site does not use decorative or content images in the current interface, so there are no missing alt-text issues.
- Colors and contrast were chosen for readability, and focus styles make keyboard navigation visible.
- Forms use matching `label for` and `id` attributes so each control has a clear accessible name.
- Navigation links and example links make sense out of context because they describe their destinations directly.

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

## TD5 Design Improvements

### Option A: Code Design Improvements

#### 1. Duplicate command-line feature logic
- Code smell / issue: `command_line.py` had duplicate logic for the deforestation and CO₂ features. Both branches repeated country resolution, default-year lookup, missing-data handling, and output formatting.
- Files and approximate lines: `command_line.py`, especially the metric selection and lookup logic around lines 26–127.
- What we changed: We introduced a small `MetricSpec` data class and a shared lookup flow (`_metric_specs`, `_selected_metric`, and `_lookup_metric`). The two CLI features now reuse one path for validation, default-year handling, and formatting instead of maintaining parallel branches.

#### 2. Duplicate repository query wrappers
- Code smell / issue: `ProductionCode/climate_repository.py` had repeated helper logic for “latest year” queries and for single-value metric queries. The forest and CO₂ methods used almost identical code with different SQL constants.
- Files and approximate lines: `ProductionCode/climate_repository.py`, especially the shared query helpers and metric accessors around lines 88–164.
- What we changed: We extracted `_latest_year` and `_metric_value` helpers so the public repository methods focus on the meaning of each query rather than repeating the same row extraction code. This keeps the metric-specific methods short and easier to maintain.

#### 3. Records-result coupling in the repository (Adapter pattern)
- Code smell / issue: `ProductionCode/climate_repository.py` still knew too much about the low-level shape of database results. It mixed business queries with details about whether a row came from the `records` library or from a simple list/dictionary test double.
- Files and approximate lines: `ProductionCode/query_adapter.py` (adapter classes around lines 1–36) and `ProductionCode/climate_repository.py` (adapter usage around lines 88–163).
- What we changed: We added a small Adapter layer (`QueryResultAdapter` and `RowAdapter`) that presents one consistent interface for query results and individual rows. The repository now asks the adapter for the first row or for a value by key instead of branching on the concrete result type. This matches the Adapter pattern discussed in class: rather than rewriting the app around a library-specific result object, we wrapped that object behind an interface that fits our existing repository code and test doubles.

### Option B: Front-End Design Improvements

#### 1. Searchable country picker
- Usability issue: The dashboard used a long country dropdown. With 235 countries, it was slow to scan and hard to use when the user already knew the country name they wanted.
- Page where we made the change: `templates/index.html` and `templates/country.html`.
- What we changed: We replaced the long dropdown with a text input backed by a `datalist`. Users can now type to filter the available countries while still getting guided suggestions from the dataset.

#### 2. Trend charts for quicker comparison
- Usability issue: The table contained useful history, but it required too much scanning to notice overall trends quickly.
- Page where we made the change: `templates/country.html` with supporting view logic in `flask_app.py` and styling in `static/styles.css`.
- What we changed: We added two small SVG trend charts, one for CO₂ per capita and one for forest change. The currently selected year is highlighted, and each chart includes a short legend with the year range and min/max values so users can compare patterns faster before reading the full table.

#### 3. Added color for clearer visual hierarchy
- Usability issue: The original interface used mostly black, white, and gray elements. While functional, the lack of color made it harder for users to quickly distinguish interactive elements (e.g. navigation and buttons) from static content.
- Page where we made the change: Global styling in `static/styles.css`, which affects all pages including `templates/index.html` and `templates/country.html`.
- What we changed: We introduced a green color palette to improve visual hierarchy and keep thematic consistency with our deforestation theme. The header, chart lines, and buttons now use green. This makes navigation elements more noticeable and allows crucial functions to stand out for better user usage.