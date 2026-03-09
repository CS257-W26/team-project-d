"""
Flask app providing a user-facing website and a JSON API for climate datasets.

Website structure:
- Homepage with a country/year form
- Dashboard page showing two metrics, trend charts, and a year-by-year table
- About page

Data for the dashboard comes from curated climate datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
)

from ProductionCode.climate_repository import ClimateRepository
from ProductionCode.db import get_db

PROJECT_NAME = "Climate Data Explorer"
UNITS = {"co2_per_capita": "t/person", "forest_change": "ha"}
_COUNTRY_PAGE_ARGS = {"entity", "year"}
_CHART_WIDTH = 360
_CHART_HEIGHT = 140
_CHART_PAD = 16

api = Blueprint("api", __name__)


@dataclass(frozen=True)
class PageOptions:
    """Shared country/year choices used across multiple pages."""

    entities: list[str]
    default_entity: str
    years: list[int]
    default_year: int


def _commas(value: Any) -> str:
    """Format an integer-like value with thousands separators."""
    return f"{int(value):,}"


def _repo() -> ClimateRepository:
    """Return the repository stored on the app config."""
    return current_app.config["REPO"]


def _normalize_entity(raw: str) -> str:
    """Normalize a user-facing entity string into a DB-friendly name."""
    return raw.replace("_", " ").strip()


def _resolve_country(repo: ClimateRepository, raw: str) -> Optional[str]:
    """Resolve a country name from a route parameter without leaking errors."""
    try:
        return repo.resolve_country(_normalize_entity(raw))
    except ValueError:
        return None


def _default_entity(entities: list[str]) -> str:
    """Choose a stable default entity for the UI."""
    return "United States" if "United States" in entities else entities[0]


def _read_year(default_year: int) -> int:
    """Read an integer year from the query string or return a default."""
    raw = (request.args.get("year") or "").strip()
    if not raw:
        return default_year
    try:
        return int(raw)
    except ValueError:
        return default_year


def _selected_year(valid_years: list[int], fallback: int) -> int:
    """Read a year and ensure it exists in a provided year list."""
    year = _read_year(fallback)
    return year if year in valid_years else fallback


def _country_page_args_are_valid() -> bool:
    """Return whether the dashboard query string only uses supported args."""
    return set(request.args).issubset(_COUNTRY_PAGE_ARGS)


def _requested_country(
    entities: list[str],
    fallback: str,
    path_entity: Optional[str],
) -> str:
    """Read a country from the path/query string or raise 404."""
    raw = request.args.get("entity") or path_entity or ""
    if not raw:
        return fallback
    country = _normalize_entity(raw)
    if country not in entities:
        abort(404)
    return country


def _requested_year(valid_years: list[int], fallback: int) -> int:
    """Read a year for the dashboard or raise 404 for invalid input."""
    raw = (request.args.get("year") or "").strip()
    if not raw:
        return fallback
    try:
        year = int(raw)
    except ValueError:
        abort(404)
    if year not in valid_years:
        abort(404)
    return year


def _api_country(entity: str) -> tuple[ClimateRepository, str]:
    """Resolve an API route parameter to a valid country or raise 404."""
    repo = _repo()
    country = _resolve_country(repo, entity)
    if not country:
        abort(404)
    return repo, country


def _api_metric_response(
    entity: str,
    latest_year_for_country: Callable[[str], int],
    value_for_year: Callable[[str, int], Optional[float]],
    unit_key: str,
):
    """Return a JSON response for a single-metric API route."""
    _unused_repo, country = _api_country(entity)
    year = _read_year(latest_year_for_country(country))
    value = value_for_year(country, year)
    if value is None:
        abort(404)
    return jsonify(
        {
            "entity": country,
            "year": year,
            "value": value,
            "unit": UNITS[unit_key],
        }
    )


def _api_dashboard_response(entity: str):
    """Return a JSON response for the dashboard API route."""
    repo, country = _api_country(entity)
    years = repo.common_years_for_country(country)
    year = _selected_year(years, repo.common_latest_year_for_country(country))
    snapshot = repo.snapshot(country, year)
    if snapshot is None:
        abort(404)
    return jsonify(
        {
            "entity": country,
            "year": year,
            "units": UNITS,
            **snapshot,
        }
    )


def _page_options(repo: ClimateRepository) -> PageOptions:
    """Return shared homepage/about choices from repository data."""
    entities = repo.countries()
    default_entity = _default_entity(entities)
    years = repo.common_years() or repo.common_years_for_country(default_entity)
    default_year = repo.common_latest_year_for_country(default_entity)
    return PageOptions(entities, default_entity, years, default_year)


def _chart_label(key: str, value: float) -> str:
    """Return a compact label for a metric value on a chart legend."""
    if key == "forest_change":
        return f"{_commas(value)} {UNITS[key]}"
    return f"{value:.1f} {UNITS[key]}"


def _chart_coords(values: list[float]) -> list[tuple[float, float]]:
    """Return SVG coordinates for a sequence of numeric values."""
    if not values:
        return []
    lowest = min(values)
    highest = max(values)
    usable_width = _CHART_WIDTH - (2 * _CHART_PAD)
    usable_height = _CHART_HEIGHT - (2 * _CHART_PAD)
    coords = []
    for index, value in enumerate(values):
        if len(values) == 1:
            x_value = _CHART_WIDTH / 2
        else:
            x_value = _CHART_PAD + (usable_width * index / (len(values) - 1))
        if highest == lowest:
            y_value = _CHART_HEIGHT / 2
        else:
            ratio = (value - lowest) / (highest - lowest)
            y_value = _CHART_HEIGHT - _CHART_PAD - (usable_height * ratio)
        coords.append((round(x_value, 1), round(y_value, 1)))
    return coords


def _trend_chart(
    rows: list[dict[str, float]],
    key: str,
    title: str,
    selected_year: int,
) -> dict[str, Any]:
    """Build SVG-ready chart data for one metric across a country's history."""
    if not rows:
        return {
            "title": title,
            "unit": UNITS[key],
            "points": "",
            "selected_x": 0.0,
            "selected_y": 0.0,
            "min_label": "",
            "max_label": "",
            "start_year": 0,
            "end_year": 0,
        }
    years = [row["year"] for row in rows]
    values = [float(row[key]) for row in rows]
    coords = _chart_coords(values)
    points = " ".join(f"{x_value},{y_value}" for x_value, y_value in coords)
    index = years.index(selected_year) if selected_year in years else len(years) - 1
    selected_x, selected_y = coords[index]
    return {
        "title": title,
        "unit": UNITS[key],
        "points": points,
        "selected_x": selected_x,
        "selected_y": selected_y,
        "min_label": _chart_label(key, min(values)),
        "max_label": _chart_label(key, max(values)),
        "start_year": years[0],
        "end_year": years[-1],
    }


def _dashboard_page_context(
    repo: ClimateRepository,
    path_entity: Optional[str],
) -> dict[str, Any]:
    """Return all validated data needed to render the dashboard."""
    entities = repo.countries()
    default_entity = _default_entity(entities)
    chosen_entity = _requested_country(entities, default_entity, path_entity)
    years = repo.common_years_for_country(chosen_entity) or repo.common_years()
    latest_year = repo.common_latest_year_for_country(chosen_entity)
    if latest_year not in years and years:
        latest_year = years[-1]
    year = _requested_year(years, latest_year)
    snapshot = repo.snapshot(chosen_entity, year)
    if snapshot is None:
        abort(404)
    series = repo.series(chosen_entity)
    return {
        "entity": chosen_entity,
        "year": year,
        "entities": entities,
        "years": years,
        "snapshot": snapshot,
        "series": series,
        "co2_chart": _trend_chart(series, "co2_per_capita", "CO₂ trend", year),
        "forest_chart": _trend_chart(series, "forest_change", "Forest change trend", year),
    }


@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: str):
    """Return forest change (ha) for a country/year."""
    repo = _repo()
    return _api_metric_response(
        entity,
        repo.forest_latest_year_for_country,
        repo.forest_value,
        "forest_change",
    )


@api.route("/co2/<string:entity>")
def api_co2(entity: str):
    """Return CO₂ per-capita (t/person) for a country/year."""
    repo = _repo()
    return _api_metric_response(
        entity,
        repo.co2_latest_year_for_country,
        repo.co2_value,
        "co2_per_capita",
    )


@api.route("/dashboard/<string:entity>")
def api_dashboard(entity: str):
    """Return both metrics for a country/year (intersection years only)."""
    return _api_dashboard_response(entity)


def _register_pages(app: Flask) -> None:
    """Register user-facing page routes."""

    @app.route("/")
    def homepage() -> str:
        """Render the website homepage."""
        options = _page_options(_repo())
        return render_template(
            "index.html",
            project=PROJECT_NAME,
            entities=options.entities,
            years=options.years,
            default_entity=options.default_entity,
            default_year=options.default_year,
        )

    @app.route("/country")
    @app.route("/country/<string:entity>")
    def country_page(entity: Optional[str] = None) -> str:
        """Render the dashboard page for a selected country/year."""
        if not _country_page_args_are_valid():
            abort(404)
        data = _dashboard_page_context(_repo(), entity)
        return render_template(
            "country.html",
            project=PROJECT_NAME,
            units=UNITS,
            **data,
        )

    @app.route("/about")
    def about_page() -> str:
        """Render a short page describing the project."""
        options = _page_options(_repo())
        return render_template(
            "about.html",
            project=PROJECT_NAME,
            entities=options.entities,
            years=options.years,
        )


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for common user mistakes."""

    @app.errorhandler(404)
    def not_found(_error):
        """Render a helpful 404 page."""
        repo = app.config.get("REPO")
        example = None
        if isinstance(repo, ClimateRepository):
            entities = repo.countries()
            if entities:
                entity = _default_entity(entities)
                year = repo.common_latest_year_for_country(entity)
                encoded = entity.replace(" ", "%20")
                example = f"/country?entity={encoded}&year={year}"
        return (
            render_template(
                "404.html",
                project=PROJECT_NAME,
                path=request.full_path.rstrip("?"),
                example=example,
            ),
            404,
        )


def create_app(db=None) -> Flask:
    """Application factory used by tests and production."""
    app = Flask(__name__)
    app.config["REPO"] = ClimateRepository(db if db is not None else get_db())
    app.jinja_env.filters["commas"] = _commas
    app.register_blueprint(api, url_prefix="/api")
    _register_pages(app)
    _register_error_handlers(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5110, debug=True)