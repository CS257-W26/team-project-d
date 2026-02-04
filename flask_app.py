"""
Flask web app

Flask app exposes the same three core features as the CLI (see command_line.py):
1. Deforestation / forest change lookup
2. CO₂ emissions per capita lookup
3. Forest change ranking
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Flask, abort, jsonify, request
from markupsafe import escape

from ProductionCode.co2 import (
    CO2_COLUMN,
    latest_year as co2_latest_year,
    load_co2_rows,
    top_emitters,
    value_for_entity_year as co2_value_for_entity_year,
)
from ProductionCode.country_list import load_country_entities
from ProductionCode.forest_change import (
    FOREST_CHANGE_COLUMN,
    count_entities_for_year,
    latest_year as forest_latest_year,
    load_forest_change_rows,
    rank_entities as forest_rank_entities,
    rank_for_entity as forest_rank_for_entity,
    value_for_entity_year as forest_value_for_entity_year,
)
from ProductionCode.output_format import RankContext, RankResult
from ProductionCode.output_format import (
    format_rank_result,
    format_single_value,
    format_top_list,
)

DEFAULT_TOP_N = 10
FOREST_UNIT = "ha"
CO2_UNIT = "t/person"

app = Flask(__name__)
api = Blueprint("api", __name__)

DATA_DIR = Path(__file__).resolve().parent / "Data"

FOREST_ROWS = load_forest_change_rows(DATA_DIR)
CO2_ROWS = load_co2_rows(DATA_DIR)
COUNTRY_ENTITIES = load_country_entities(DATA_DIR)


def normalize_entity_param(raw: str) -> str:
    """normalize an entity provided in the url path"""
    return raw.strip().replace("_", " ").replace("-", " ")


def parse_optional_int(raw: Optional[str], param_name: str) -> Optional[int]:
    """parse an optional integer query parameter"""
    if raw is None:
        return None

    cleaned = raw.strip()
    if cleaned == "":
        return None

    try:
        return int(cleaned)
    except ValueError as exc:
        raise ValueError(f"{param_name} must be an integer.") from exc


def parse_optional_positive_int(raw: Optional[str], param_name: str) -> Optional[int]:
    """parse an optional positive integer query parameter"""
    value = parse_optional_int(raw, param_name=param_name)
    if value is not None and value <= 0:
        raise ValueError(f"{param_name} must be a positive integer.")
    return value


def parse_bool(raw: Optional[str], default: bool = False) -> bool:
    """parse a boolean query parameter"""
    if raw is None:
        return default

    cleaned = raw.strip().lower()
    if cleaned in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if cleaned in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def parse_order(raw: Optional[str], default: str = "loss") -> str:
    """parse the order parameter for forest ranking routes"""
    if raw is None or raw.strip() == "":
        return default

    order = raw.strip().lower()
    if order not in {"loss", "gain"}:
        raise ValueError("order must be 'loss' or 'gain'.")
    return order


def render_page(title: str, inner_html: str) -> str:
    """return a complete html document using a simple centered layout"""
    styles = """
    <style>
      body {
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        margin: 0;
        padding: 0;
      }
      .container {
        max-width: 980px;
        margin: 0 auto;
        padding: 40px 20px;
        text-align: center;
      }
      .card {
        display: inline-block;
        width: min(820px, 100%);
        text-align: left;
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
      }
      code, pre {
        background: #f6f8fa;
        border-radius: 6px;
      }
      code {
        padding: 2px 6px;
      }
      pre {
        padding: 12px;
        overflow-x: auto;
      }
      h1, h2 {
        margin: 0 0 12px 0;
      }
      h2 {
        margin-top: 24px;
      }
      ul {
        margin: 8px 0 0 24px;
      }
      label {
        display: block;
        font-weight: 600;
        margin-top: 12px;
      }
      input, select {
        width: 100%;
        box-sizing: border-box;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 8px;
        font-size: 1rem;
      }
      button {
        margin-top: 14px;
        padding: 10px 14px;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #fff;
        cursor: pointer;
      }
      a {
        word-break: break-word;
      }
      .small {
        color: #666;
        font-size: 0.95rem;
      }
    </style>
    """

    return (
        "<!doctype html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='utf-8' />"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        f"<title>{escape(title)}</title>"
        f"{styles}"
        "</head>"
        "<body>"
        f"<div class='container'>{inner_html}</div>"
        "</body>"
        "</html>"
    )


def render_homepage() -> str:
    """render the homepage with usage instructions and an interactive url builder"""
    inner = (
        "<h1>Team Project D – Flask App</h1>"
        "<p>This web app lets you query the same datasets as the CLI.</p>"
        "<div class='card'>"
        "<h2>Features</h2>"
        "<ul>"
        "<li><strong>Deforestation</strong>: annual change in forest area</li>"
        "<li><strong>CO₂</strong>: annual CO₂ emissions per capita</li>"
        "<li><strong>Ranking</strong>: rank entities by forest change</li>"
        "</ul>"
        "</div>"
        "<div class='card'>"
        "<h2>How to use</h2>"
        "<p>All routes accept <code>year</code> as an optional query parameter.</p>"
        "<p>To include aggregates like <code>World</code>, pass "
        "<code>include_aggregates=1</code>. (Default: countries only.)</p>"
        "<h3>HTML routes</h3>"
        "<ul>"
        "<li><code>/deforestation/&lt;entity&gt;</code> (single value)</li>"
        "<li><code>/deforestation</code> (top list; params: year, top, order)</li>"
        "<li><code>/co2/&lt;entity&gt;</code> (single value)</li>"
        "<li><code>/co2</code> (top list; params: year, top)</li>"
        "<li><code>/ranking/&lt;entity&gt;</code> (rank for entity; params: year, order)</li>"
        "<li><code>/ranking</code> (top list; params: year, top, order)</li>"
        "</ul>"
        "<p class='small'>Tip: you can write "
        "<code>United_States</code> instead of <code>United States</code>.</p>"
        "</div>"
        "<div class='card'>"
        "<h2>Try it</h2>"
        "<p>Leave entity blank to see a list output; fill it to see a single-entity result.</p>"
        "<form id='query-form' onsubmit='return goToQuery();'>"
        "  <label for='feature'>feature</label>"
        "  <select id='feature' name='feature'>"
        "    <option value='deforestation'>deforestation</option>"
        "    <option value='co2'>co2</option>"
        "    <option value='ranking'>ranking</option>"
        "  </select>"
        "  <label for='entity'>entity (optional)</label>"
        "  <input id='entity' name='entity' type='text' value='United States' />"
        "  <label for='year'>year (optional)</label>"
        "  <input id='year' name='year' type='number' placeholder='e.g. 2021' />"
        "  <label for='top'>top (for list outputs)</label>"
        "  <input id='top' name='top' type='number' value='10' min='1' />"
        "  <label for='order'>order (forest lists / ranking)</label>"
        "  <select id='order' name='order'>"
        "    <option value='loss' selected>loss</option>"
        "    <option value='gain'>gain</option>"
        "  </select>"
        "  <label for='include_aggregates'>include_aggregates</label>"
        "  <select id='include_aggregates' name='include_aggregates'>"
        "    <option value='0' selected>0 (default)</option>"
        "    <option value='1'>1</option>"
        "  </select>"
        "  <button type='submit'>Go</button>"
        "</form>"
        "<p>Generated URL: <a id='generated-link' href='#'>(fill the form)</a></p>"
        "</div>"
        "<div class='card'>"
        "<h2>Examples</h2>"
        "<ul>"
        "<li><a href='/deforestation/United_States?year=2021'>"
        "/deforestation/United_States?year=2021</a></li>"
        "<li><a href='/co2/Canada?year=2021'>/co2/Canada?year=2021</a></li>"
        "<li><a href='/ranking/Brazil?year=2021&order=loss'>"
        "/ranking/Brazil?year=2021&amp;order=loss</a></li>"
        "<li><a href='/deforestation?year=2021&top=5&order=loss'>"
        "/deforestation?year=2021&amp;top=5&amp;order=loss</a></li>"
        "</ul>"
        "<h3>API examples</h3>"
        "<ul>"
        "<li><a href='/api/deforestation/United_States?year=2021'>"
        "/api/deforestation/United_States?year=2021</a></li>"
        "<li><a href='/api/co2?year=2021&top=3'>/api/co2?year=2021&amp;top=3</a></li>"
        "</ul>"
        "</div>"
        "<script>"
        "function slugifyEntity(raw) {\n"
        "  if (!raw) return '';\n"
        "  return raw.trim().replace(/\\s+/g, '_');\n"
        "}\n"
        "function buildUrl() {\n"
        "  const feature = document.getElementById('feature').value;\n"
        "  const entityRaw = document.getElementById('entity').value;\n"
        "  const entity = slugifyEntity(entityRaw);\n"
        "  let url = '/' + encodeURIComponent(feature);\n"
        "  if (entity) url += '/' + encodeURIComponent(entity);\n"
        "  const year = document.getElementById('year').value;\n"
        "  const top = document.getElementById('top').value;\n"
        "  const order = document.getElementById('order').value;\n"
        "  const includeAgg = document.getElementById('include_aggregates').value;\n"
        "  const params = [];\n"
        "  if (year) params.push('year=' + encodeURIComponent(year));\n"
        "  if (!entity && top) params.push('top=' + encodeURIComponent(top));\n"
        "  if (feature !== 'co2') params.push('order=' + encodeURIComponent(order));\n"
        "  if (includeAgg === '1') params.push('include_aggregates=1');\n"
        "  if (params.length) url += '?' + params.join('&');\n"
        "  return url;\n"
        "}\n"
        "function updateLink() {\n"
        "  const link = document.getElementById('generated-link');\n"
        "  const url = buildUrl();\n"
        "  link.href = url;\n"
        "  link.textContent = url;\n"
        "}\n"
        "function goToQuery() {\n"
        "  window.location.href = buildUrl();\n"
        "  return false;\n"
        "}\n"
        "['feature','entity','year','top','order','include_aggregates'].forEach((id) => {\n"
        "  document.getElementById(id).addEventListener('input', updateLink);\n"
        "  document.getElementById(id).addEventListener('change', updateLink);\n"
        "});\n"
        "updateLink();\n"
        "</script>"
    )
    return render_page("Team Project D – Flask App", inner)


def render_result_page(title: str, body_text: str) -> str:
    """render a tiny page showing one pre-formatted result block"""
    inner = (
        "<div class='card'>"
        f"<h1>{escape(title)}</h1>"
        f"<pre>{escape(body_text)}</pre>"
        "<p><a href='/'>Back to instructions</a></p>"
        "</div>"
    )
    return render_page(title, inner)


def _forest_value(
    entity_query: str,
    year: Optional[int],
    include_aggregates: bool,
) -> Tuple[str, int, float]:
    """return (entity, year_used, value_ha) for forest change"""
    only_countries = not include_aggregates
    return forest_value_for_entity_year(
        rows=FOREST_ROWS,
        entity_query=entity_query,
        year=year,
        only_countries=only_countries,
    )


def _forest_list(
    year: Optional[int],
    top_n: int,
    order: str,
    include_aggregates: bool,
) -> Tuple[int, List[Tuple[str, float]]]:
    """return (year_used, ranked_rows) for a forest change list"""
    only_countries = not include_aggregates

    year_used = year
    if year_used is None:
        year_used = forest_latest_year(FOREST_ROWS, only_countries=only_countries)

    ranked = forest_rank_entities(
        rows=FOREST_ROWS,
        year=year_used,
        order=order,
        top_n=top_n,
        only_countries=only_countries,
    )
    return year_used, ranked


def _co2_value(
    entity_query: str,
    year: Optional[int],
    include_aggregates: bool,
) -> Tuple[str, int, float]:
    """return (entity, year_used, value_tonnes_per_capita) for co2"""
    only_countries = not include_aggregates
    return co2_value_for_entity_year(
        rows=CO2_ROWS,
        entity_query=entity_query,
        year=year,
        only_countries=only_countries,
        country_entities=COUNTRY_ENTITIES,
    )


def _co2_list(
    year: Optional[int],
    top_n: int,
    include_aggregates: bool,
) -> Tuple[int, List[Tuple[str, float]]]:
    """return (year_used, ranked_rows) for a CO₂ top-emitters list"""
    only_countries = not include_aggregates

    year_used = year
    if year_used is None:
        year_used = co2_latest_year(
            CO2_ROWS,
            only_countries=only_countries,
            country_entities=COUNTRY_ENTITIES,
        )

    ranked = top_emitters(
        rows=CO2_ROWS,
        year=year_used,
        top_n=top_n,
        only_countries=only_countries,
        country_entities=COUNTRY_ENTITIES,
    )
    return year_used, ranked


def _ranking_value(
    entity_query: str,
    year: Optional[int],
    order: str,
    include_aggregates: bool,
) -> RankResult:
    """return a RankResult for a single entity's forest-change ranking"""
    only_countries = not include_aggregates
    entity, year_used, rank, value = forest_rank_for_entity(
        rows=FOREST_ROWS,
        entity_query=entity_query,
        year=year,
        order=order,
        only_countries=only_countries,
    )
    total = count_entities_for_year(
        rows=FOREST_ROWS,
        year=year_used,
        only_countries=only_countries,
    )
    context = RankContext(metric=FOREST_CHANGE_COLUMN, unit=FOREST_UNIT, order=order)
    return RankResult(
        entity=entity,
        year=year_used,
        context=context,
        rank=rank,
        total=total,
        value=value,
    )


def _ranking_list(
    year: Optional[int],
    top_n: int,
    order: str,
    include_aggregates: bool,
) -> Tuple[int, List[Tuple[str, float]]]:
    """return (year_used, ranked_rows) for a forest-change ranking list"""
    return _forest_list(
        year=year,
        top_n=top_n,
        order=order,
        include_aggregates=include_aggregates,
    )


@app.route("/")
def homepage() -> str:
    """homepage with instructions and examples"""
    return render_homepage()


@app.route("/deforestation")
@app.route("/deforestation/<string:entity>")
def deforestation(entity: Optional[str] = None) -> str:
    """forest change feature (single value or top list)"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        order = parse_order(request.args.get("order"), default="loss")
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            name, year_used, value_ha = _forest_value(
                entity_query=entity_query,
                year=year,
                include_aggregates=include_aggregates,
            )
            text = format_single_value(
                entity=name,
                year=year_used,
                metric=FOREST_CHANGE_COLUMN,
                value=value_ha,
                unit=FOREST_UNIT,
            )
            return render_result_page("Deforestation (forest change)", text)

        year_used, ranked = _forest_list(
            year=year,
            top_n=top_n,
            order=order,
            include_aggregates=include_aggregates,
        )
        title = (
            f"Top {min(top_n, len(ranked))} entities for {FOREST_CHANGE_COLUMN} in "
            f"{year_used} (order={order})"
        )
        text = format_top_list(title=title, rows=ranked, unit=FOREST_UNIT)
        return render_result_page("Deforestation list", text)

    except ValueError as exc:
        abort(404, description=str(exc))


@app.route("/co2")
@app.route("/co2/<string:entity>")
def co2_route(entity: Optional[str] = None) -> str:
    """co2 per-capita feature (single value or top emitters list)"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            name, year_used, value_t = _co2_value(
                entity_query=entity_query,
                year=year,
                include_aggregates=include_aggregates,
            )
            text = format_single_value(
                entity=name,
                year=year_used,
                metric=CO2_COLUMN,
                value=value_t,
                unit=CO2_UNIT,
            )
            return render_result_page("CO₂ per-capita", text)

        year_used, ranked = _co2_list(
            year=year,
            top_n=top_n,
            include_aggregates=include_aggregates,
        )
        title = f"Top {min(top_n, len(ranked))} entities for {CO2_COLUMN} in {year_used}:"
        text = format_top_list(title=title, rows=ranked, unit=CO2_UNIT)
        return render_result_page("CO₂ top emitters", text)

    except ValueError as exc:
        abort(404, description=str(exc))


@app.route("/ranking")
@app.route("/ranking/<string:entity>")
def ranking(entity: Optional[str] = None) -> str:
    """forest change ranking feature (entity rank or top list)"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        order = parse_order(request.args.get("order"), default="loss")
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            result = _ranking_value(
                entity_query=entity_query,
                year=year,
                order=order,
                include_aggregates=include_aggregates,
            )
            text = format_rank_result(result)
            return render_result_page("Ranking result", text)

        year_used, ranked = _ranking_list(
            year=year,
            top_n=top_n,
            order=order,
            include_aggregates=include_aggregates,
        )
        title = f"Forest change ranking for {year_used} (order={order}):"
        text = format_top_list(title=title, rows=ranked, unit=FOREST_UNIT)
        return render_result_page("Ranking list", text)

    except ValueError as exc:
        abort(404, description=str(exc))


def _json_rows(rows: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    """convert (entity, value) rows into JSON-ready dicts"""
    result: List[Dict[str, Any]] = []
    for entity, value in rows:
        result.append({"entity": entity, "value": value})
    return result


@api.route("/deforestation")
@api.route("/deforestation/<string:entity>")
def api_deforestation(entity: Optional[str] = None):
    """api endpoint for forest change queries"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        order = parse_order(request.args.get("order"), default="loss")
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            name, year_used, value_ha = _forest_value(
                entity_query=entity_query,
                year=year,
                include_aggregates=include_aggregates,
            )
            return jsonify(
                {
                    "feature": "deforestation",
                    "metric": FOREST_CHANGE_COLUMN,
                    "entity": name,
                    "year": year_used,
                    "value": value_ha,
                    "unit": FOREST_UNIT,
                }
            )

        year_used, ranked = _forest_list(
            year=year,
            top_n=top_n,
            order=order,
            include_aggregates=include_aggregates,
        )
        return jsonify(
            {
                "feature": "deforestation",
                "metric": FOREST_CHANGE_COLUMN,
                "year": year_used,
                "order": order,
                "top_n": min(top_n, len(ranked)),
                "unit": FOREST_UNIT,
                "rows": _json_rows(ranked),
            }
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


@api.route("/co2")
@api.route("/co2/<string:entity>")
def api_co2(entity: Optional[str] = None):
    """api endpoint for CO₂ per-capita queries"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            name, year_used, value_t = _co2_value(
                entity_query=entity_query,
                year=year,
                include_aggregates=include_aggregates,
            )
            return jsonify(
                {
                    "feature": "co2",
                    "metric": CO2_COLUMN,
                    "entity": name,
                    "year": year_used,
                    "value": value_t,
                    "unit": CO2_UNIT,
                }
            )

        year_used, ranked = _co2_list(
            year=year,
            top_n=top_n,
            include_aggregates=include_aggregates,
        )
        return jsonify(
            {
                "feature": "co2",
                "metric": CO2_COLUMN,
                "year": year_used,
                "top_n": min(top_n, len(ranked)),
                "unit": CO2_UNIT,
                "rows": _json_rows(ranked),
            }
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


@api.route("/ranking")
@api.route("/ranking/<string:entity>")
def api_ranking(entity: Optional[str] = None):
    """api endpoint for forest-change ranking queries"""
    try:
        year = parse_optional_int(request.args.get("year"), "year")
        include_aggregates = parse_bool(
            request.args.get("include_aggregates"),
            default=False,
        )
        order = parse_order(request.args.get("order"), default="loss")
        top_n = parse_optional_positive_int(request.args.get("top"), "top") or DEFAULT_TOP_N

        if entity:
            entity_query = normalize_entity_param(entity)
            result = _ranking_value(
                entity_query=entity_query,
                year=year,
                order=order,
                include_aggregates=include_aggregates,
            )
            return jsonify(
                {
                    "feature": "ranking",
                    "metric": result.context.metric,
                    "entity": result.entity,
                    "year": result.year,
                    "order": order,
                    "rank": result.rank,
                    "total": result.total,
                    "value": result.value,
                    "unit": result.context.unit,
                }
            )

        year_used, ranked = _ranking_list(
            year=year,
            top_n=top_n,
            order=order,
            include_aggregates=include_aggregates,
        )
        return jsonify(
            {
                "feature": "ranking",
                "metric": FOREST_CHANGE_COLUMN,
                "year": year_used,
                "order": order,
                "top_n": min(top_n, len(ranked)),
                "unit": FOREST_UNIT,
                "rows": _json_rows(ranked),
            }
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


@app.errorhandler(404)
def page_not_found(e):
    """helpful 404 page with working examples"""
    description = getattr(e, "description", "Page not found.")
    inner = (
        "<div class='card'>"
        "<h1>404 - Not Found</h1>"
        f"<p>{escape(description)}</p>"
        "<p>Try one of these working examples:</p>"
        "<ul>"
        "<li><a href='/'>/</a></li>"
        "<li><a href='/deforestation/United_States?year=2021'>"
        "/deforestation/United_States?year=2021</a></li>"
        "<li><a href='/co2/Canada?year=2021'>/co2/Canada?year=2021</a></li>"
        "<li><a href='/ranking/Brazil?year=2021&order=loss'>"
        "/ranking/Brazil?year=2021&amp;order=loss</a></li>"
        "<li><a href='/api/deforestation/United_States?year=2021'>"
        "/api/deforestation/United_States?year=2021</a></li>"
        "</ul>"
        "</div>"
    )
    return render_page("404 - Not Found", inner), 404


@app.errorhandler(500)
def internal_server_error(e):
    """500 handler for unexpected errors"""
    _ = e
    inner = (
        "<div class='card'>"
        "<h1>500 - Internal Server Error</h1>"
        "<p>Eek, a Caterpie!</p>"
        "</div>"
    )
    return render_page("500 - Internal Server Error", inner), 500


if "api" not in app.blueprints:
    app.register_blueprint(api, url_prefix="/api")


if __name__ == "__main__":
    app.run()
