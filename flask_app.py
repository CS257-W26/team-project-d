"""For flask queries."""
from flask import Flask, render_template as render
from ProductionCode.datasource import DataSource

app = Flask(__name__)
ds = DataSource()

@app.route("/")
def homepage():
    """Homepage."""
    return render("homepage.html")

@app.route('/<data>/<name>/<int:year_1>/<int:year_2>')
@app.route('/<data>/<name>/<int:year_1>')
def entity(data: str, name: str, year_1: int, year_2: int = None):
    """
    Handle regular entity flask queries.
    Parameters:
        data (str): data type
        name (str): entity
        year_1 (int): year
        year_2 (None): optional second year
    """
    func = {"forest-change": ds.query_forest, "co2": ds.query_co2, "temps": ds.query_temps}
    csv = {"forest-change": "Forest Change", "co2": "Capita CO2 Emissions",
           "temps": "Relative To 1861-1890"}
    try:
        if year_2 is not None:
            vals = func[data](["range", name, year_1, year_2])
            if vals is not None:
                val_1 = list(vals[0].values())[2]
                val_2 = list(vals[1].values())[2]
                return render("regions.html", year_1 = year_1, year_2 = year_2,
                data = csv[data], val_1 = val_1, val_2 = val_2, name = name)
            return "Information does not exist for input."
        vals = func[data]([name, year_1])[0]
        if vals is not None:
            val_1 = list(vals.values())[2]
            return render("regions.html", year_1 = year_1, year_2 = "No 2nd year.",
            data = csv[data], val_1 = val_1, val_2 = "No 2nd year.", name = name)
        return "Information does not exist for input."
    except (ValueError, KeyError, IndexError) as e:
        return f"{e} Please check homepage for help."

@app.route('/<data>/<int:year>')
def entities(data: str, year: int):
    """
    Handle entity list flask queries.
    Parameters:
        data (str): data type
        year (int): year
    """
    # not working
    func = {"forest-change": ds.query_forest, "co2": ds.query_co2, "temps": ds.query_temps}
    try:
        val = func[data](["list", year])
        vals = []
        for i in val:
            vals.append(i["entity"])
        values = ", ".join(vals)
        return f"{values}"
    except (ValueError, KeyError, IndexError) as e:
        return f"{e} Please check homepage for help."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5209)
