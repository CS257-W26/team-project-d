"""
Flask app providing a user-facing website and a JSON API for climate datasets.

Website structure:
- Homepage with a country/year form
- Dashboard page showing two metrics (deforestation & CO2) and a year-by-year table
- About page

Data is queried from a PostgreSQL database on stearns via the records library.
"""

from __future__ import annotations

from typing import Any, Optional

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


def _selected_entity(
    entities: list[str],
    fallback: str,
    path_entity: Optional[str],
) -> str:
    """read a valid entity from the path/query string or fall back"""
    raw = request.args.get("entity") or path_entity or ""
    normalized = _normalize_entity(raw)
    return normalized if normalized in entities else fallback


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


@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: str):
    """return forest change (ha) for a country/year"""
    repo = _repo()
    country = _resolve_country(repo, entity)
    if not country:
        abort(404)
    year = _read_year(repo.forest_latest_year_for_country(country))
    value = repo.forest_value(country, year)
    if value is None:
        abort(404)
    return jsonify(
        {
            "entity": country,
            "year": year,
            "value": value,
            "unit": UNITS["forest_change"],
        }
    )


@api.route("/co2/<string:entity>")
def api_co2(entity: str):
    """return CO₂ per-capita (t/person) for a country/year"""
    repo = _repo()
    country = _resolve_country(repo, entity)
    if not country:
        abort(404)
    year = _read_year(repo.co2_latest_year_for_country(country))
    value = repo.co2_value(country, year)
    if value is None:
        abort(404)
    return jsonify(
        {
            "entity": country,
            "year": year,
            "value": value,
            "unit": UNITS["co2_per_capita"],
        }
    )


@api.route("/dashboard/<string:entity>")
def api_dashboard(entity: str):
    """return both metrics for a country/year (intersection years only)"""
    repo = _repo()
    country = _resolve_country(repo, entity)
    if not country:
        abort(404)
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
        default_entity = _default_entity(entities)
        chosen_entity = _selected_entity(entities, default_entity, entity)
        years = repo.common_years_for_country(chosen_entity) or repo.common_years()
        year = _selected_year(years, repo.common_latest_year_for_country(chosen_entity))
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
                path=request.path,
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
