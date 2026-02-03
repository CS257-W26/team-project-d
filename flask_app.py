"""
Team D
This page keeps the codes for Flask and API interface.
"""
import os
from pathlib import Path
from flask import Flask, request, jsonify, Blueprint, abort

from ProductionCode.forest_change import (
    load_forest_change_rows,
    value_for_entity_year,
    rank_entities,
)

from ProductionCode.co2 import (
    load_co2_rows,
    value_for_entity_year as co2_value_for_entity_year,
    top_emitters as co2_top_emitters,
)


def create_app(test_config=None):
    """
    App factory: lets us create the app both for normal use and for tests.
    """
    app = Flask(__name__)

    # Allow tests to override config
    if test_config is not None:
        app.config.update(test_config)

    base_dir = Path(__file__).resolve().parent
    default_data_dir = base_dir / "Data"

    data_dir = app.config.get("DATA_DIR", default_data_dir)

    data_dir = Path(data_dir)

    forest_rows = load_forest_change_rows(data_dir)
    co2_rows = load_co2_rows(data_dir)

    # Create API blueprint (required by rubric)
    api = Blueprint("api", __name__)

    # Helper function
    def get_year_or_400():
        """
        Helper function for 400 error.
        If year is missing/invalid, abort with a 400.
        """
        year = request.args.get("year", type=int)
        if year is None:
            abort(400, description="Missing or invalid 'year'. Example: ?year=2020")
        return year

    @app.route("/")
    def home():
        """
        Homepage with introduction and instructions.
        """
        return (
            "<h1>Carbon & Forests Dashboard</h1>"
            "<p>Please insert a country and a year to check deforestation or CO2.</p>"
            "<p>Try these:</p>"
            "<ul>"
            "<li>/deforestation/Afghanistan?year=2020</li>"
            "<li>/deforestation/top?year=2020&top=10</li>"
            "<li>/co2/Afghanistan?year=2020</li>"
            "<li>/co2/top?year=2020&top=10</li>"
            "</ul>"
        )

    @app.route("/deforestation/<entity>")
    def deforestation_for_entity(entity):
        """
        Feature: returns deforestation value of a country in a specific year.
        URL example: /deforestation/Afghanistan?year=2020
        """
        year = get_year_or_400()
        value = value_for_entity_year(forest_rows, entity, year)

        return(
            f"<h2>Deforestation for {entity} in {year}</h2>"
            f"<p>Forest change value: {value}</p>"
            "<p><a href='/'>Back home</a></p>"
        )

    @app.route("/deforestation/top")
    def top_deforestation():
        """
        Feature: ranking of countries by deforestation value.
        URL example: /deforestation/top?year=2020&top=10
        """
        year = get_year_or_400()
        top_n = request.args.get("top", default=10, type=int)
        results = rank_entities(forest_rows, year=year, top_n=top_n)

        items = "".join(f"<li>{r}</li>" for r in results)

        return(
            f"<h2>Top {top_n} deforestation results for {year}</h2>"
            f"<ol>{items}</ol>"
            "<p><a href='/'>Back home</a></p>"
        )

    @app.route("/co2/<entity>")
    def co2_for_entity(entity):
        """
        Feature: returns CO2 value of a country in a specific year.
        """
        year = get_year_or_400()
        value = co2_value_for_entity_year(co2_rows, entity, year)

        return(
            f"<h2>CO2 for {entity} in {year}</h2>"
            f"<p>CO2 value: {value}</p>"
            "<p><a href='/'>Back home</a></p>"
        )

    @app.route("/co2/top")
    def top_co2():
        """
        Feature: shows CO2 emission ranking of countries in a certain year.
        """
        year = get_year_or_400()
        top_n = request.args.get("top", default=10, type=int)
        results = co2_top_emitters(co2_rows, year=year, top_n=top_n)

        items = "".join(f"<li>{r}</li>" for r in results)

        return(
            f"<h2>Top {top_n} CO2 emitters for {year}</h2>"
            f"<ol>{items}</ol>"
            "<p><a href='/'>Back home</a></p>"
        )

    # API routes

    @api.route("/deforestation/<entity>")
    def api_deforestation_for_entity(entity):
        """
        API corresponding to deforestation entry
        """
        year = get_year_or_400()
        value = value_for_entity_year(forest_rows, entity, year)
        return jsonify({"entity": entity, "year": year, "forest_change": value})

    @api.route("/deforestation/top")
    def api_top_deforestation():
        """
        API corresponding to deforestation ranking
        """
        year = get_year_or_400()
        top_n = request.args.get("top", default=10, type=int)
        results = rank_entities(forest_rows, year=year, top_n=top_n)
        return jsonify({"year": year, "top": top_n, "results": results})

    @api.route("/co2/<entity>")
    def api_co2_for_entity(entity):
        """
        API corresponding to CO2 emission search
        """
        year = get_year_or_400()
        value = co2_value_for_entity_year(co2_rows, entity, year)
        return jsonify({"entity": entity, "year": year, "co2": value})

    @api.route("/co2/top")
    def api_top_co2():
        """
        API corresponding to CO2 emission ranking
        """
        year = get_year_or_400()
        top_n = request.args.get("top", default=10, type=int)
        results = co2_top_emitters(co2_rows, year=year, top_n=top_n)
        return jsonify({"year": year, "top": top_n, "results": results})

    # Register blueprint under /api (required)
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(400)
    def bad_request(e):
        """
        error handler for 400 errors if year input turns out to be invalid
        """
        return(
            "<h1>400 - Bad Request</h1>"
            f"<p>{e}</p>"
            "<p>Try: /deforestation/Afghanistan?year=2020</p>"
            "<p><a href='/'>Back home</a></p>",
            400,
        )

    @app.errorhandler(404)
    def not_found(e):
        """
        error handler for invalid URL
        """
        return(
            "<h1>404 - Page Not Found</h1>"
            "<p>That URL doesn't exist.</p>"
            "<p><a href='/'>Back home</a></p>",
            404,
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
