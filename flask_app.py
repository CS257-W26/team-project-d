"""For flask queries."""
from flask import Flask, render_template, request
from ProductionCode.datasource import DataSource

app = Flask(__name__)
ds = DataSource()

@app.route("/co2")
def co2_page():
    return render_template("co2.html")

@app.route("/co2/results")
def co2_results():
    country = request.args.get("name")
    year = request.args.get("year")
    if not country:
        return "Please enter a country."
    if not year:
        return "Please enter a year."
    try:
        data = ds.query_regions("co2", "co2_per_capita", [country, year])
        if not data:
            return "No CO₂ data found for that input."
        return render_template("country.html", data=data)
    except ValueError:
        return "Invalid input. Please check your country and year."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5209)
