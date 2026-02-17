"""For database access."""
import records
import ProductionCode.psql_config as config

class DataSource:
    """DataSource class for database queries"""
    def __init__(self):
        connect = f"postgresql://{config.user}:{config.password}@localhost:5432/{config.database}"
        self.db = records.Database(connect)

    def query_forest(self, args) -> list:
        """
        Handle forest-change queries.
        Parameters:
            args (list): user input
        """
        return self.query_call("forest_change", "Annual_Forest_Change", args)

    def query_co2(self, args) -> list:
        """
        Handle CO2 queries.
        Parameters:
            args (list): user input
        """
        return self.query_call("co2", "co2_per_capita", args)

    def query_temps(self, args) -> list:
        """
        Handle temperature queries.
        Parameters:
            args (list): user input
        """
        data = ", ".join(["Relative_To_1861_1890", "Lower_Bound", "Upper_Bound"])
        return self.query_call("temps", data, args)

    def query_call(self, table: str, data: str, args: list) -> list:
        """
        Call queries based on user input.
        Parameters:
            table (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if args[0] in ["top", "bottom"]:
            return self.query_order_n(table, data, args)
        if args[0] == "range":
            return self.query_range(table, data, args[1:])
        if args[0] == "list":
            return self.query_list(table, args[1:])
        if args[0] == "aggregate":
            print("here")
            return self.query_aggregator(table, data, args[1:])
        return self.query_regions(table, data, args)

    def query_regions(self, table: str, data: str, args) -> list:
        """
        Search entity data in set of given year.
        Parameters:
            table (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) != 2:
            raise ValueError("Invalid argument.")
        if not args[1].isdigit():
            raise ValueError(f"{args[1]} is an invalid year input.")
        vals = self.db.query(f"SELECT Entity, Year, {data} FROM {table}").all(as_dict=True)
        if any(r["entity"] == args[0] for r in vals):
            if not any(r["entity"] == args[0] and r["year"] == int(args[1]) for r in vals):
                raise ValueError(f"Year {args[1]} does not exist for {args[0]}.")
            return [r for r in vals if r["entity"] == args[0] and r["year"] == int(args[1])]
        raise ValueError(f"Entity {args[0]} does not exist in dataset.")

    def query_order_n(self, table: str, data: str, args: list) -> list:
        """
        Search top or bottom N in set of given year.
        Parameters:
            table (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) != 3:
            raise ValueError("Invalid argument.")
        if not args[1].isdigit() or not args[2].isdigit():
            raise ValueError(f"{args[1]} or {args[2]} are not integers.")
        years = self.db.query(f"SELECT Year FROM {table}").all(as_dict=True)
        if not any(r["year"] == int(args[2]) for r in years): 
            raise ValueError(f"Year {args[2]} does not exist in dataset.")
        order = "DESC" if str(args[0]).startswith("top") else "ASC"
        entry = f"""SELECT Entity, Year, {data} FROM {table} WHERE Year = :year ORDER BY {data} {order} LIMIT :n"""
        vals = self.db.query(entry, year=args[2], n=args[1]).all(as_dict=True)
        return vals

    def query_range(self, table: str, data: str, args: list) -> list:
        """
        Search entity data in set of two given years.
        Parameters:
            table (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) != 3:
            raise ValueError("Invalid argument.")
        vals = [self.query_regions(table, data, [args[0], i]) for i in [args[1], args[2]]]
        return vals[0] + vals[1]

    def query_list(self, table: str, args: list) -> list:
        """
        List entities in set of given year.
        Parameters:
            table (str): data to query
            args (list): user input
        """
        if len(args) != 1:
            raise ValueError("Invalid argument.")
        if not args[0].isdigit():
            raise ValueError(f"{args[0]} is an invalid year input.")
        vals = self.db.query(f"SELECT Entity, Year FROM {table}").all(as_dict=True)
        if any(r["year"] == int(args[0]) for r in vals):
            return [r for r in vals if r["year"] == int(args[0])]
        raise ValueError(f"Year {args[0]} does not exist in dataset.")

    def query_aggregator(self, table: str, data: str, args: list) -> list:
        """
        Search data for entities in set of given year.
        Parameters:
            table (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) < 2:
            raise ValueError("Invalid argument.")
        if not args[-1].isdigit():
            raise ValueError(f"{args[-1]} is an invalid year input.")
        vals = self.db.query(f"SELECT Entity, Year, {data} FROM {table}").all(as_dict=True)
        if any(r["year"] == int(args[-1]) for r in vals):
            for i in args[0:-1]:
                if not any(r["entity"] == i for r in vals):
                    raise ValueError(f"Entity {i} does not exist in dataset.")
                if not any(r["entity"] == i and r["year"] == int(args[-1]) for r in vals):
                    raise ValueError(f"Entity {i} does not exist for {args[-1]}.")
            return [r for r in vals if r["year"] == int(args[-1]) and r["entity"] in args[:-1]]
        raise ValueError(f"Year {args[-1]} does not exist in dataset.")
