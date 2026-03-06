"""
Flask app providing a user-facing website and a JSON API for climate datasets.

Website structure:
- Homepage with a country/year form
- Dashboard page showing two metrics (deforestation & CO2) and a year-by-year table
- About page

Data for the dashboard comes from curated climate datasets.
"""

from __future__ import annotations

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

api = Blueprint("api", __name__)


def _commas(value: Any) -> str:
    """format an integer-like value with thousands separators"""
    return f"{int(value):,}"


def _repo() -> ClimateRepository:
    """convenience accessor for the repository stored on the app config"""
    return current_app.config["REPO"]


def _normalize_entity(raw: str) -> str:
    """normalize a user-facing entity string into a DB-friendly name"""
    return raw.replace("_", " ").strip()


def _resolve_country(repo: ClimateRepository, raw: str) -> Optional[str]:
    """resolve a country name from a route parameter without leaking errors"""
    try:
        return repo.resolve_country(_normalize_entity(raw))
    except ValueError:
        return None


def _default_entity(entities: list[str]) -> str:
    """choose a stable default entity for the UI"""
    return "United States" if "United States" in entities else entities[0]


def _read_year(default_year: int) -> int:
    """read an integer year from the query string or return a default"""
    raw = (request.args.get("year") or "").strip()
    if not raw:
        return default_year
    try:
        return int(raw)
    except ValueError:
        return default_year


def _selected_year(valid_years: list[int], fallback: int) -> int:
    """read a year and ensure it exists in a provided year list"""
    year = _read_year(fallback)
    return year if year in valid_years else fallback


def _country_page_args_are_valid() -> bool:
    """return whether the dashboard query string only uses supported args"""
    return set(request.args).issubset(_COUNTRY_PAGE_ARGS)


def _requested_country(
    entities: list[str],
    fallback: str,
    path_entity: Optional[str],
) -> str:
    """read a country from the path/query string or raise 404"""
    raw = request.args.get("entity") or path_entity or ""
    if not raw:
        return fallback
    country = _normalize_entity(raw)
    if country not in entities:
        abort(404)
    return country


def _requested_year(valid_years: list[int], fallback: int) -> int:
    """read a year for the dashboard or raise 404 for invalid input"""
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
    """resolve an API route parameter to a valid country or raise 404"""
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
    """return a JSON response for a single-metric API route"""
    _repo_unused, country = _api_country(entity)
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
    """return a JSON response for the dashboard API route"""
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


@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: str):
    """return forest change (ha) for a country/year"""
    repo = _repo()
    return _api_metric_response(
        entity,
        repo.forest_latest_year_for_country,
        repo.forest_value,
        "forest_change",
    )


@api.route("/co2/<string:entity>")
def api_co2(entity: str):
    """return CO₂ per-capita (t/person) for a country/year"""
    repo = _repo()
    return _api_metric_response(
        entity,
        repo.co2_latest_year_for_country,
        repo.co2_value,
        "co2_per_capita",
    )


@api.route("/dashboard/<string:entity>")
def api_dashboard(entity: str):
    """return both metrics for a country/year (intersection years only)"""
    return _api_dashboard_response(entity)


def _register_pages(app: Flask) -> None:
    """register user-facing page routes"""

    @app.route("/")
    def homepage() -> str:
        """render the website homepage"""
        repo = _repo()
        entities = repo.countries()
        default_entity = _default_entity(entities)
        years = repo.common_years() or repo.common_years_for_country(default_entity)
        return render_template(
            "index.html",
            project=PROJECT_NAME,
            entities=entities,
            years=years,
            default_entity=default_entity,
            default_year=repo.common_latest_year_for_country(default_entity),
        )

    @app.route("/country")
    @app.route("/country/<string:entity>")
    def country_page(entity: Optional[str] = None) -> str:
        """render the dashboard page for a selected country/year"""
        repo = _repo()
        entities = repo.countries()
        if not _country_page_args_are_valid():
            abort(404)
        default_entity = _default_entity(entities)
        chosen_entity = _requested_country(entities, default_entity, entity)
        years = repo.common_years_for_country(chosen_entity) or repo.common_years()
        latest_year = repo.common_latest_year_for_country(chosen_entity)
        if latest_year not in years and years:
            latest_year = years[-1]
        year = _requested_year(years, latest_year)
        snapshot = repo.snapshot(chosen_entity, year)
        if snapshot is None:
            abort(404)

        return render_template(
            "country.html",
            project=PROJECT_NAME,
            entity=chosen_entity,
            year=year,
            entities=entities,
            years=years,
            units=UNITS,
            snapshot=snapshot,
            series=repo.series(chosen_entity),
        )

    @app.route("/about")
    def about_page() -> str:
        """render a short page describing the project"""
        repo = _repo()
        entities = repo.countries()
        default_entity = _default_entity(entities)
        years = repo.common_years() or repo.common_years_for_country(default_entity)
        return render_template(
            "about.html",
            project=PROJECT_NAME,
            entities=entities,
            years=years,
        )


def _register_error_handlers(app: Flask) -> None:
    """register error handlers for common user mistakes"""

    @app.errorhandler(404)
    def not_found(_error):
        """render a helpful 404 page"""
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
    """application factory used by tests and production"""
    app = Flask(__name__)
    app.config["REPO"] = ClimateRepository(db if db is not None else get_db())
    app.jinja_env.filters["commas"] = _commas
    app.register_blueprint(api, url_prefix="/api")
    _register_pages(app)
    _register_error_handlers(app)
    return app


if __name__ == "__main__":
    create_app().run()
