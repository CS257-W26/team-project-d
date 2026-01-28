[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/w6LgLvZq)
# CS257-TeamTemplate
Template for long-term team projects for CS257 Software Design

Group D Team Members: Milly, Simon, Amery

# Team Project D – Command Line Interface (Component 1)

This repo contains a **Python command-line app** that lets you query and explore our
environmental datasets (Our World in Data CSV exports).

Supported features (3 independent CLI features):

1. **Deforestation / forest change lookup** (`--deforestation`)  
   Look up the *annual change in forest area* for a country in a specific year.
   If `--year` is omitted, the app defaults to the **latest year available for that country**.

2. **CO₂ per-capita lookup** (`--co2`)  
   Look up *annual CO₂ emissions per capita* for a country in a specific year.
   If `--year` is omitted, the app defaults to the **latest year available for that country**.

3. **Forest change ranking** (`--ranking`)  
   Rank countries by annual change in forest area (largest loss or largest gain).

The CLI includes `-h/--help` usage and an automated `unittest` test suite.

## Usage

Run the built-in help:

```bash
python3 command_line.py -h
```

By default, the program reads CSV files from `./Data`. You can override the
data directory with `--data-dir`.

### Feature 1: Forest change (deforestation proxy)

```bash
# Value lookup (explicit year)
python3 command_line.py --deforestation Brazil --year 2020

# Value lookup (default year = latest for that country)
python3 command_line.py --deforestation Brazil

# List/ranking output (no country provided)
python3 command_line.py --deforestation --year 2020 --top 10
```

### Feature 2: CO₂ emissions per capita

```bash
# Value lookup (explicit year)
python3 command_line.py --co2 Canada --year 2021

# Value lookup (default year = latest for that country)
python3 command_line.py --co2 Canada

# List output (no country provided)
python3 command_line.py --co2 --year 2020 --top 10
```

### Feature 3: Forest change ranking

```bash
# Rank for a single country
python3 command_line.py --ranking Brazil --year 2020

# List the top 10 forest losses in a year
python3 command_line.py --ranking --year 2020 --order loss --top 10

# List the top 10 forest gains in a year
python3 command_line.py --ranking --year 2020 --order gain --top 10
```

### Aggregates vs. Countries

By default, results are **countries only**. To include aggregates (e.g., *World*,
*Africa*), add:

```bash
python3 command_line.py --co2 --year 2020 --top 10 --include-aggregates
```

## Running Tests

From the repo root:

```bash
python3 -m unittest discover -s Tests -v
```

## Data Files

The CLI expects these files to exist in the data directory (default `./Data`):

- `annual-change-forest-area.csv`
- `co-emissions-per-capita.csv`

## Dependencies

This project uses **only the Python standard library**.

### Production code

- `argparse` – build the command-line interface and `-h/--help` output
- `csv` – read the dataset CSV files
- `dataclasses` – define typed row/result objects
- `pathlib` – handle filesystem paths for datasets
- `typing` – type hints for better function design
- `difflib`, `re`, `unicodedata` – implement forgiving entity-name matching
- `sys` – print errors to stderr and return non-zero exit codes

### Tests

- `unittest` – automated test framework
- `contextlib.redirect_stdout / redirect_stderr` and `io.StringIO` – capture CLI output
- `tempfile` – create temporary CSV files for I/O edge-case tests

No third-party packages are required.
>>>>>>> e8e476f (CLI)
