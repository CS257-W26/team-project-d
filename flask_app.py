from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request

def _metric_from_row(row: Dict[str, Any]) -> Tuple[str, Any]:
    """Extract the non-entity/year metric from a records row dict."""
    for k, v in row.items():
        if k not in ("entity", "year", "code"):
            return k, v
    return "value", None


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def create_app(db: Optional[object] = None, testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = testing

    if db is None:
        from ProductionCode.co2_queries import DataSource  # imported lazily
        ds = DataSource()
    else:
        ds = db

    def get_countries() -> List[str]:
        # Prefer forest_change list; fall back to co2 if needed.
        for table in ("forest_change", "co2"):
            try:
                rows = ds.db.query(f"SELECT DISTINCT Entity FROM {table} ORDER BY Entity").all(as_dict=True)
                return [r["entity"] for r in rows if r.get("entity")]
            except Exception:
                continue
        return []

    @app.get("/")
    def home():
        return render_template("homepage.html", title="Carbon & Forests Dashboard")

    @app.get("/about")
    def about_page():
        return render_template("about.html", title="About")

    @app.get("/deforestation")
    def deforestation_page():
        country = request.args.get("country")
        year = request.args.get("year")
        message = None

        if country or year:
            if not country or not year:
                message = "please select a valid country or year"
            else:
                try:
                    rows = ds.query_forest([country, year])
                    if not rows:
                        message = "please select a valid country or year"
                    else:
                        _, val = _metric_from_row(rows[0])
                        message = f"Deforestation area of {country} in {int(year)} is {val} ha"
                except Exception:
                    message = "please select a valid country or year"

        return render_template(
            "deforestation.html",
            title="Deforestation lookup",
            countries=get_countries(),
            country=country,
            year=year,
            message=message,
        )

    @app.get("/co2")
    def co2_page():
        country = request.args.get("country")
        year = request.args.get("year")
        message = None

        if country or year:
            if not country or not year:
                message = "please select a valid country or year"
            else:
                try:
                    rows = ds.query_co2([country, year])
                    if not rows:
                        message = "please select a valid country or year"
                    else:
                        _, val = _metric_from_row(rows[0])
                        message = f"CO₂ emissions per capita of {country} in {int(year)} is {val}"
                except Exception:
                    message = "please select a valid country or year"

        return render_template(
            "co2.html",
            title="CO₂ lookup",
            countries=get_countries(),
            country=country,
            year=year,
            message=message,
        )

    def _rank_country(country: str, year: int) -> Tuple[Optional[int], Optional[int]]:
        def_rows = ds.db.query(
            "SELECT Entity, Annual_Forest_Change FROM forest_change WHERE Year = :y",
            y=year,
        ).all(as_dict=True)
        def_vals = [(r["entity"], _safe_float(r.get("annual_forest_change"))) for r in def_rows]
        def_vals = [(e, v) for e, v in def_vals if v is not None]
        def_vals.sort(key=lambda t: t[1])
        def_rank = None
        for i, (e, _) in enumerate(def_vals, start=1):
            if e == country:
                def_rank = i
                break

        co2_rows = ds.db.query(
            "SELECT Entity, co2_per_capita FROM co2 WHERE Year = :y",
            y=year,
        ).all(as_dict=True)
        co2_vals = [(r["entity"], _safe_float(r.get("co2_per_capita"))) for r in co2_rows]
        co2_vals = [(e, v) for e, v in co2_vals if v is not None]
        co2_vals.sort(key=lambda t: t[1], reverse=True)
        co2_rank = None
        for i, (e, _) in enumerate(co2_vals, start=1):
            if e == country:
                co2_rank = i
                break

        return def_rank, co2_rank

    @app.get("/ranking")
    def ranking_page():
        country = request.args.get("country")
        year_raw = request.args.get("year")
        message = None

        if country or year_raw:
            if not country or not year_raw:
                message = "please select a valid country or year"
            else:
                try:
                    year = int(year_raw)
                    def_rank, co2_rank = _rank_country(country, year)
                    if def_rank is None or co2_rank is None:
                        message = "please select a valid country or year"
                    else:
                        message = f"In {year}, {country} ranks #{def_rank} in deforestation and #{co2_rank} in CO₂ emissions per capita."
                except Exception:
                    message = "please select a valid country or year"

        return render_template(
            "ranking.html",
            title="Ranking",
            countries=get_countries(),
            country=country,
            year=year_raw,
            message=message,
        )

    @app.get("/api/deforestation")
    def api_deforestation():
        country = request.args.get("country")
        year = request.args.get("year")
        if not country or not year:
            return jsonify({"error": "country and year are required"}), 400
        rows = ds.query_forest([country, year])
        if not rows:
            return jsonify({"error": "not found"}), 404
        _, val = _metric_from_row(rows[0])
        return jsonify({"country": country, "year": int(year), "deforestation_ha": val})

    @app.get("/api/co2")
    def api_co2():
        country = request.args.get("country")
        year = request.args.get("year")
        if not country or not year:
            return jsonify({"error": "country and year are required"}), 400
        rows = ds.query_co2([country, year])
        if not rows:
            return jsonify({"error": "not found"}), 404
        _, val = _metric_from_row(rows[0])
        return jsonify({"country": country, "year": int(year), "co2_per_capita": val})

    @app.get("/api/ranking")
    def api_ranking():
        country = request.args.get("country")
        year_raw = request.args.get("year")
        if not country or not year_raw:
            return jsonify({"error": "country and year are required"}), 400
        year = int(year_raw)
        def_rank, co2_rank = _rank_country(country, year)
        if def_rank is None or co2_rank is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"country": country, "year": year, "deforestation_rank": def_rank, "co2_rank": co2_rank})

    # Custom 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", title="Page not found"), 404

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5110, debug=True)
