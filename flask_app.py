"""
Flask app providing HTML pages and a JSON API for the climate datasets.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from flask import Blueprint, Flask, abort, current_app, jsonify, render_template, request

from ProductionCode.climate_repository import CO2_COLUMN, FOREST_CHANGE_COLUMN, ClimateRepository
from ProductionCode.db import get_db
from ProductionCode.numbers import format_number
from ProductionCode.output_format import RankContext, RankResult
from ProductionCode.output_format import format_rank_result, format_single_value

DEFAULT_TOP_N = 10
FOREST_UNIT = "ha"
CO2_UNIT = "t/person"

ONLY_COUNTRIES = True

pages = Blueprint("pages", __name__)
api = Blueprint("api", __name__)

_EXAMPLES = [
    {
        "label": "Deforestation for United States (2021)",
        "href": "/deforestation/United_States?year=2021",
    },
    {"label": "CO₂ per capita for Canada (2021)", "href": "/co2/Canada?year=2021"},
    {
        "label": "Forest change ranking for Brazil (2021, loss)",
        "href": "/ranking/Brazil?year=2021&order=loss",
    },
    {
        "label": "JSON API example (deforestation)",
        "href": "/api/deforestation/United_States?year=2021",
    },
]


def parse_optional_int(raw: Optional[str], param_name: str) -> Optional[int]:
    """parse an optional integer query parameter"""
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{param_name} must be an integer.") from exc


def parse_optional_positive_int(raw: Optional[str], param_name: str) -> Optional[int]:
    """parse an optional positive integer query parameter"""
    value = parse_optional_int(raw, param_name)
    if value is not None and value <= 0:
        raise ValueError(f"{param_name} must be a positive integer.")
    return value


def parse_order(raw: Optional[str], default: str = "loss") -> str:
    """parse loss/gain ordering"""
    value = (raw or "").strip().lower() or default
    if value in {"loss", "gain"}:
        return value
    raise ValueError("order must be 'loss' or 'gain'.")


def normalize_entity_param(entity_param: str) -> str:
    """convert a URL path entity into a dataset-style entity name"""
    return entity_param.replace("_", " ").replace("-", " ").strip()


def _repo() -> ClimateRepository:
    """return the configured repository or raise RuntimeError"""
    repo = current_app.config.get("REPO")
    if repo is None:
        raise RuntimeError("Repository is not configured.")
    return repo


def _year() -> Optional[int]:
    """read year from query string"""
    return parse_optional_int(request.args.get("year"), "year")


def _top() -> int:
    """read top from query string"""
    return parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N


def _order() -> str:
    """read order from query string"""
    return parse_order(request.args.get("order"), default="loss")


def _entity(path_entity: Optional[str]) -> Optional[str]:
    """return an entity name from path param or query string"""
    raw = (path_entity or request.args.get("entity") or "").strip()
    return normalize_entity_param(raw) if raw else None


def _rows_view(rows: Sequence[Tuple[str, float]]) -> List[dict]:
    """convert ranked rows into a template-friendly shape"""
    return [
        {"rank": idx, "entity": entity, "value": format_number(value)}
        for idx, (entity, value) in enumerate(rows, start=1)
    ]


def _value_view(metric: str, unit: str, name: str, year: int, value: float) -> dict:
    """build a display dict for a single numeric value"""
    return {
        "metric": metric,
        "unit": unit,
        "entity": name,
        "year": year,
        "value": format_number(value),
        "summary": format_single_value(name, year, metric, value, unit),
    }


def _rank_view(result: RankResult) -> dict:
    """build a display dict for a single ranking result"""
    summary = format_rank_result(result)
    return {
        "entity": result.entity,
        "year": result.year,
        "order": result.context.order,
        "rank": result.rank,
        "total": result.total,
        "value": format_number(result.value),
        "unit": result.context.unit,
        "summary": summary,
    }

def _form_defaults() -> dict:
    """return current query-string values for form defaults"""
    return {
        "entity": request.args.get("entity", ""),
        "year": request.args.get("year", ""),
        "top": request.args.get("top", ""),
        "order": request.args.get("order", ""),
    }


def _forest_value_data(entity: str) -> Tuple[str, int, float]:
    """return (entity, year, value) for forest-change"""
    return _repo().forest_value_for_entity_year(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        only_countries=ONLY_COUNTRIES,
    )


def _co2_value_data(entity: str) -> Tuple[str, int, float]:
    """return (entity, year, value) for CO2 per-capita"""
    return _repo().co2_value_for_entity_year(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        only_countries=ONLY_COUNTRIES,
    )


def _forest_list_data() -> Tuple[int, str, int, Sequence[Tuple[str, float]]]:
    """return (year, order, top_n, rows) for forest-change top lists"""
    order = _order()
    top_n = _top()
    year = _year() or _repo().forest_latest_year(ONLY_COUNTRIES)
    rows = _repo().forest_rank_entities(
        year=year,
        order=order,
        top_n=top_n,
        only_countries=ONLY_COUNTRIES,
    )
    return year, order, top_n, rows


def _co2_list_data() -> Tuple[int, int, Sequence[Tuple[str, float]]]:
    """return (year, top_n, rows) for CO2 per-capita top lists"""
    top_n = _top()
    year = _year() or _repo().co2_latest_year(ONLY_COUNTRIES)
    rows = _repo().co2_top_emitters(
        year=year,
        top_n=top_n,
        only_countries=ONLY_COUNTRIES,
    )
    return year, top_n, rows


def _ranking_data(entity: str) -> RankResult:
    """return a RankResult for forest-change ranking"""
    order = _order()
    name, year, rank, value = _repo().forest_rank_for_entity(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        order=order,
        only_countries=ONLY_COUNTRIES,
    )
    total = _repo().forest_count_entities_for_year(year=year, only_countries=ONLY_COUNTRIES)
    ctx = RankContext(metric=FOREST_CHANGE_COLUMN, unit=FOREST_UNIT, order=order)
    return RankResult(name, year, ctx, rank, total, value)

def _top_list_title(
    metric: str,
    year: int,
    top_n: int,
    rows: Sequence[Tuple[str, float]],
    order: Optional[str] = None,
) -> str:
    """build the title line for a formatted top list"""
    prefix = f"Top {min(top_n, len(rows))} countries for {metric} in {year}"
    return f"{prefix} (order={order})" if order is not None else prefix


@pages.route("/")
def homepage():
    """styled homepage with forms and example links"""
    return render_template("home.html", active_page="home", examples=_EXAMPLES)


@pages.route("/about")
def about():
    """short about/help page"""
    return render_template("about.html", active_page="about")


@pages.route("/deforestation")
@pages.route("/deforestation/<string:entity>")
def deforestation(entity: Optional[str] = None):
    """user-facing page for forest-change"""
    try:
        name = _entity(entity)
        if name:
            entity_name, year, value = _forest_value_data(name)
            result = _value_view(FOREST_CHANGE_COLUMN, FOREST_UNIT, entity_name, year, value)
            return render_template(
                "deforestation.html",
                active_page="deforestation",
                result=result,
                form=_form_defaults(),
            )

        year, order, top_n, rows = _forest_list_data()
        title = _top_list_title(FOREST_CHANGE_COLUMN, year, top_n, rows, order)
        list_result = {"title": title, "unit": FOREST_UNIT, "rows": _rows_view(rows)}
        return render_template(
            "deforestation.html",
            active_page="deforestation",
            list_result=list_result,
            form=_form_defaults(),
        )
    except ValueError as exc:
        abort(404, description=str(exc))


@pages.route("/co2")
@pages.route("/co2/<string:entity>")
def co2(entity: Optional[str] = None):
    """user-facing page for CO2 per-capita"""
    try:
        name = _entity(entity)
        if name:
            entity_name, year, value = _co2_value_data(name)
            result = _value_view(CO2_COLUMN, CO2_UNIT, entity_name, year, value)
            return render_template(
                "co2.html",
                active_page="co2",
                result=result,
                form=_form_defaults(),
            )

        year, top_n, rows = _co2_list_data()
        title = _top_list_title(CO2_COLUMN, year, top_n, rows)
        list_result = {"title": title, "unit": CO2_UNIT, "rows": _rows_view(rows)}
        return render_template(
            "co2.html",
            active_page="co2",
            list_result=list_result,
            form=_form_defaults(),
        )
    except ValueError as exc:
        abort(404, description=str(exc))


@pages.route("/ranking")
@pages.route("/ranking/<string:entity>")
def ranking(entity: Optional[str] = None):
    """user-facing page for forest-change ranking"""
    try:
        name = _entity(entity)
        if name:
            ranking_result = _ranking_data(name)
            result = _rank_view(ranking_result)
            return render_template(
                "ranking.html",
                active_page="ranking",
                result=result,
                form=_form_defaults(),
            )

        year, order, _, rows = _forest_list_data()
        title = f"Forest change ranking for {year} (order={order})"
        list_result = {"title": title, "unit": FOREST_UNIT, "rows": _rows_view(rows)}
        return render_template(
            "ranking.html",
            active_page="ranking",
            list_result=list_result,
            form=_form_defaults(),
        )
    except ValueError as exc:
        abort(404, description=str(exc))


def _api_error(exc: Exception):
    """return a consistent json error payload"""
    return jsonify({"error": str(exc)}), 404


def _json_rows(rows: Sequence[Tuple[str, float]]) -> List[dict]:
    """convert rows into a json-friendly shape"""
    return [{"entity": entity, "value": value} for entity, value in rows]


@api.route("/deforestation")
@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: Optional[str] = None):
    """json endpoint for forest-change queries"""
    try:
        if entity:
            name, year, value = _forest_value_data(entity)
            return jsonify(
                {
                    "feature": "deforestation",
                    "metric": FOREST_CHANGE_COLUMN,
                    "entity": name,
                    "year": year,
                    "value": value,
                    "unit": FOREST_UNIT,
                }
            )

        year, order, top_n, rows = _forest_list_data()
        return jsonify(
            {
                "feature": "deforestation",
                "metric": FOREST_CHANGE_COLUMN,
                "year": year,
                "order": order,
                "top_n": min(top_n, len(rows)),
                "unit": FOREST_UNIT,
                "rows": _json_rows(rows),
            }
        )
    except ValueError as exc:
        return _api_error(exc)


@api.route("/co2")
@api.route("/co2/<string:entity>")
def api_co2(entity: Optional[str] = None):
    """json endpoint for CO2 per-capita queries"""
    try:
        if entity:
            name, year, value = _co2_value_data(entity)
            return jsonify(
                {
                    "feature": "co2",
                    "metric": CO2_COLUMN,
                    "entity": name,
                    "year": year,
                    "value": value,
                    "unit": CO2_UNIT,
                }
            )

        year, top_n, rows = _co2_list_data()
        return jsonify(
            {
                "feature": "co2",
                "metric": CO2_COLUMN,
                "year": year,
                "top_n": min(top_n, len(rows)),
                "unit": CO2_UNIT,
                "rows": _json_rows(rows),
            }
        )
    except ValueError as exc:
        return _api_error(exc)


@api.route("/ranking")
@api.route("/ranking/<string:entity>")
def api_ranking(entity: Optional[str] = None):
    """json endpoint for forest-change ranking queries"""
    try:
        if entity:
            result = _ranking_data(entity)
            return jsonify(
                {
                    "feature": "ranking",
                    "metric": FOREST_CHANGE_COLUMN,
                    "entity": result.entity,
                    "year": result.year,
                    "order": result.context.order,
                    "rank": result.rank,
                    "total": result.total,
                    "value": result.value,
                    "unit": result.context.unit,
                }
            )

        year, order, top_n, rows = _forest_list_data()
        return jsonify(
            {
                "feature": "ranking",
                "metric": FOREST_CHANGE_COLUMN,
                "year": year,
                "order": order,
                "top_n": min(top_n, len(rows)),
                "unit": FOREST_UNIT,
                "rows": _json_rows(rows),
            }
        )
    except ValueError as exc:
        return _api_error(exc)


def internal_server_error(err):
    """return the custom 500 page"""
    _ = err
    return render_template("500.html", active_page=""), 500


def register_error_handlers(app: Flask) -> None:
    """register html error handlers"""

    @app.errorhandler(404)
    def not_found(err):
        msg = getattr(err, "description", "Page not found.")
        return (
            render_template("404.html", message=msg, examples=_EXAMPLES, active_page=""),
            404,
        )

    app.register_error_handler(500, internal_server_error)


def create_app(db=None) -> Flask:
    """application factory used by tests and production"""
    app = Flask(__name__)
    app.config["REPO"] = ClimateRepository(db if db is not None else get_db())
    app.register_blueprint(pages)
    app.register_blueprint(api, url_prefix="/api")
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    create_app().run()
