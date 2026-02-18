"""
Flask app providing HTML pages and a JSON API for the climate datasets.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from flask import Blueprint, Flask, abort, current_app, jsonify, request
from markupsafe import escape

from ProductionCode.climate_repository import CO2_COLUMN, FOREST_CHANGE_COLUMN, ClimateRepository
from ProductionCode.db import get_db
from ProductionCode.output_format import RankContext, RankResult
from ProductionCode.output_format import format_rank_result, format_single_value, format_top_list

DEFAULT_TOP_N = 10
FOREST_UNIT = "ha"
CO2_UNIT = "t/person"

pages = Blueprint("pages", __name__)
api = Blueprint("api", __name__)

_HOME_BODY = (
    "<h1>Climate Data Explorer</h1>"
    "<p>Try these examples:</p>"
    "<ul>"
    "<li><a href='/deforestation/United_States?year=2021'>"
    "/deforestation/United_States?year=2021</a></li>"
    "<li><a href='/co2/Canada?year=2021'>/co2/Canada?year=2021</a></li>"
    "<li><a href='/ranking/Brazil?year=2021&amp;order=loss'>"
    "/ranking/Brazil?year=2021&amp;order=loss</a></li>"
    "<li><a href='/api/deforestation/United_States?year=2021'>"
    "/api/deforestation/United_States?year=2021</a></li>"
    "</ul>"
)


def render_page(title: str, body_html: str) -> str:
    """wrap body_html in a minimal html page"""
    safe_title = escape(title)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{safe_title}</title></head><body>{body_html}</body></html>"
    )


def render_pre_page(title: str, heading: str, text: str) -> str:
    """render a simple page with a heading and <pre> block"""
    body = (
        f"<h1>{escape(heading)}</h1><pre>{escape(text)}</pre>"
        "<p><a href='/'>Home</a></p>"
    )
    return render_page(title, body)


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


def parse_bool(raw: Optional[str], default: bool = False) -> bool:
    """parse a loose boolean query parameter"""
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true"}:
        return True
    if value in {"0", "false"}:
        return False
    return default


def parse_order(raw: Optional[str], default: str = "loss") -> str:
    """parse loss/gain ordering"""
    value = (raw or "").strip().lower() or default
    if value in {"loss", "gain"}:
        return value
    raise ValueError("order must be 'loss' or 'gain'.")


def normalize_entity_param(entity_param: str) -> str:
    """convert url path entity into a dataset-style entity name"""
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


def _only_countries() -> bool:
    """return true unless include_aggregates is enabled"""
    return not parse_bool(request.args.get("include_aggregates"), default=False)


def _json_rows(rows: Sequence[Tuple[str, float]]) -> List[dict]:
    """convert rows into a JSON-friendly shape"""
    return [{"entity": entity, "value": value} for entity, value in rows]


def _value_payload(
    feature: str, metric: str, unit: str, entity: str, year: int, value: float
) -> dict:
    """build a consistent json payload for single-value endpoints"""
    return {
        "feature": feature,
        "metric": metric,
        "entity": entity,
        "year": year,
        "value": value,
        "unit": unit,
    }


def _list_payload(
    feature: str,
    metric: str,
    unit: str,
    year: int,
    rows: Sequence[Tuple[str, float]],
    top_n: int,
    order: Optional[str] = None,
) -> dict:
    """build a consistent json payload for top-list endpoints"""
    payload = {
        "feature": feature,
        "metric": metric,
        "year": year,
        "top_n": min(top_n, len(rows)),
        "unit": unit,
        "rows": _json_rows(rows),
    }
    if order is not None:
        payload["order"] = order
    return payload


def _ranking_payload(
    entity: str, year: int, order: str, rank: int, total: int, value: float
) -> dict:
    """build a json payload for a single-entity ranking"""
    return {
        "feature": "ranking",
        "metric": FOREST_CHANGE_COLUMN,
        "entity": entity,
        "year": year,
        "order": order,
        "rank": rank,
        "total": total,
        "value": value,
        "unit": FOREST_UNIT,
    }


def _forest_value_data(entity: str) -> Tuple[str, int, float]:
    """return (entity, year, value) for forest-change"""
    return _repo().forest_value_for_entity_year(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        only_countries=_only_countries(),
    )


def _co2_value_data(entity: str) -> Tuple[str, int, float]:
    """return (entity, year, value) for co2 per-capita"""
    return _repo().co2_value_for_entity_year(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        only_countries=_only_countries(),
    )


def _forest_list_data() -> Tuple[int, str, int, Sequence[Tuple[str, float]]]:
    """return (year, order, top_n, rows) for forest-change top lists"""
    only = _only_countries()
    order = _order()
    top_n = _top()
    year = _year() or _repo().forest_latest_year(only)
    rows = _repo().forest_rank_entities(year=year, order=order, top_n=top_n, only_countries=only)
    return year, order, top_n, rows


def _co2_list_data() -> Tuple[int, int, Sequence[Tuple[str, float]]]:
    """return (year, top_n, rows) for co2 per-capita top lists"""
    only = _only_countries()
    top_n = _top()
    year = _year() or _repo().co2_latest_year(only)
    rows = _repo().co2_top_emitters(year=year, top_n=top_n, only_countries=only)
    return year, top_n, rows


def _ranking_data(entity: str) -> Tuple[str, int, str, int, int, float]:
    """return (entity, year, order, rank, total, value) for a ranking"""
    only = _only_countries()
    order = _order()
    name, year, rank, value = _repo().forest_rank_for_entity(
        entity_query=normalize_entity_param(entity),
        year=_year(),
        order=order,
        only_countries=only,
    )
    total = _repo().forest_count_entities_for_year(year=year, only_countries=only)
    return name, year, order, rank, total, value


def _top_list_title(
    metric: str,
    year: int,
    top_n: int,
    rows: Sequence[Tuple[str, float]],
    order: Optional[str] = None,
) -> str:
    """build the title line for a formatted top list"""
    prefix = f"Top {min(top_n, len(rows))} entities for {metric} in {year}"
    return f"{prefix} (order={order})" if order is not None else prefix


@pages.route("/")
def homepage():
    """homepage with a few working example links"""
    return render_page("Home", _HOME_BODY)


@pages.route("/deforestation")
@pages.route("/deforestation/<string:entity>")
def deforestation(entity: Optional[str] = None):
    """html endpoint for forest-change queries"""
    try:
        if entity:
            name, year, value = _forest_value_data(entity)
            text = format_single_value(name, year, FOREST_CHANGE_COLUMN, value, FOREST_UNIT)
            return render_pre_page("Deforestation", "Deforestation", text)

        year, order, top_n, rows = _forest_list_data()
        title = _top_list_title(FOREST_CHANGE_COLUMN, year, top_n, rows, order)
        text = format_top_list(title, rows, FOREST_UNIT)
        return render_pre_page("Deforestation", f"Deforestation {year}", text)
    except ValueError as exc:
        abort(404, description=str(exc))


@pages.route("/co2")
@pages.route("/co2/<string:entity>")
def co2(entity: Optional[str] = None):
    """html endpoint for co2 per-capita queries"""
    try:
        if entity:
            name, year, value = _co2_value_data(entity)
            text = format_single_value(name, year, CO2_COLUMN, value, CO2_UNIT)
            return render_pre_page("CO₂", "CO₂ per capita", text)

        year, top_n, rows = _co2_list_data()
        title = _top_list_title(CO2_COLUMN, year, top_n, rows)
        text = format_top_list(title, rows, CO2_UNIT)
        return render_pre_page("CO₂", f"CO₂ per capita {year}", text)
    except ValueError as exc:
        abort(404, description=str(exc))


@pages.route("/ranking")
@pages.route("/ranking/<string:entity>")
def ranking(entity: Optional[str] = None):
    """html endpoint for forest-change ranking queries"""
    try:
        if entity:
            name, year, order, rank, total, value = _ranking_data(entity)
            ctx = RankContext(metric=FOREST_CHANGE_COLUMN, unit=FOREST_UNIT, order=order)
            text = format_rank_result(RankResult(name, year, ctx, rank, total, value))
            return render_pre_page("Ranking", "Ranking", text)

        year, order, top_n, rows = _forest_list_data()
        title = f"Forest change ranking for {year} (order={order})"
        text = format_top_list(title, rows, FOREST_UNIT)
        return render_pre_page("Ranking", f"Ranking {year}", text)
    except ValueError as exc:
        abort(404, description=str(exc))


def _api_error(exc: Exception):
    """return a consistent json error payload"""
    return jsonify({"error": str(exc)}), 404


@api.route("/deforestation")
@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: Optional[str] = None):
    """json endpoint for forest-change queries"""
    try:
        if entity:
            name, year, value = _forest_value_data(entity)
            payload = _value_payload(
                "deforestation", FOREST_CHANGE_COLUMN, FOREST_UNIT, name, year, value
            )
            return jsonify(payload)

        year, order, top_n, rows = _forest_list_data()
        payload = _list_payload(
            "deforestation", FOREST_CHANGE_COLUMN, FOREST_UNIT, year, rows, top_n, order
        )
        return jsonify(payload)
    except ValueError as exc:
        return _api_error(exc)


@api.route("/co2")
@api.route("/co2/<string:entity>")
def api_co2(entity: Optional[str] = None):
    """json endpoint for co2 per-capita queries"""
    try:
        if entity:
            name, year, value = _co2_value_data(entity)
            return jsonify(_value_payload("co2", CO2_COLUMN, CO2_UNIT, name, year, value))

        year, top_n, rows = _co2_list_data()
        payload = _list_payload("co2", CO2_COLUMN, CO2_UNIT, year, rows, top_n)
        return jsonify(payload)
    except ValueError as exc:
        return _api_error(exc)


@api.route("/ranking")
@api.route("/ranking/<string:entity>")
def api_ranking(entity: Optional[str] = None):
    """json endpoint for forest-change ranking queries"""
    try:
        if entity:
            name, year, order, rank, total, value = _ranking_data(entity)
            return jsonify(_ranking_payload(name, year, order, rank, total, value))

        year, order, top_n, rows = _forest_list_data()
        payload = _list_payload(
            "ranking", FOREST_CHANGE_COLUMN, FOREST_UNIT, year, rows, top_n, order
        )
        return jsonify(payload)
    except ValueError as exc:
        return _api_error(exc)


def _not_found_body(message: str) -> str:
    """return the 404 page html"""
    return (
        "<h1>404 - Not Found</h1>"
        f"<p>{escape(message)}</p>"
        "<p>Try one of these working examples:</p>"
        "<ul>"
        "<li><a href='/'>/</a></li>"
        "<li><a href='/deforestation/United_States?year=2021'>"
        "/deforestation/United_States?year=2021</a></li>"
        "</ul>"
    )


def internal_server_error(err):
    """return the custom 500 page"""
    _ = err
    body = "<h1>500 - Internal Server Error</h1><p>Eek, a Caterpie!</p>"
    return render_page("500 - Internal Server Error", body), 500


def register_error_handlers(app: Flask) -> None:
    """register minimal HTML error handlers"""
    @app.errorhandler(404)
    def not_found(err):
        msg = getattr(err, "description", "Page not found.")
        return render_page("404 - Not Found", _not_found_body(msg)), 404

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
