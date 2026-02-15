import records
import ProductionCode.psql_config as config

class DataSource:
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
        return self.query_call("co2", "Annual_CO2_Capita_Emissions", args)

    def query_temps(self, args) -> list:
        """
        Handle temperature queries.
        Parameters:
            args (list): user input
        """
        data = ", ".join(["Relative_To_1861_1890", "Lower_Bound", "Upper_Bound"])
        return self.query_call("temps", data, args)
    
    def query_call(self, type: str, data: str, args: list) -> list:
        """
        Call queries based on user input.
        Parameters:
            type (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if args[0] in ["top-gain", "top-emitters", "lowest-emitters", "lowest-gain"]:
            return self.query_order_N(type, data, args)
        elif args[0] == "range":
            return self.query_range(type, data, args[1:])
        elif args[0] == "list":
            return self.query_list(type, args[1:])
        elif args[0] == "aggregate":
            return self.query_aggregator(type, data, args[1:])
        else:
            return self.query_regions(type, data, args)

    def query_regions(self, type: str, data: str, args) -> list:
        """
        Search entity data in set of given year.
        Parameters:
            type (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) != 2:
            raise ValueError("Invalid argument.")
        vals = self.db.query(f"SELECT Entity, Year, {data} FROM {type}").all(as_dict=True)
        if any(r["Entity"] == args[0] for r in vals):
            if not any(r["Entity"] == args[0] and r["Year"] == args[1] for r in vals):
                raise ValueError(f"Year {args[1]} does not exist for {args[0]}.")
            return [r for r in vals if r["Entity"] == args[0] and r["Year"] == args[1]]
        raise ValueError(f"Entity {args[0]} does not exist in dataset.")
        
    def query_order_N(self, type: str, data: str, args: list) -> list:
        """
        Search top or bottom N in set of given year.
        Parameters:
            type (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) < 3:
            raise ValueError("Invalid argument.")
        years = self.db.query(f"SELECT Year FROM {type}").all(as_dict=True)
        if not any(r["Year"] == args[1] for r in years):
            raise ValueError(f"Year {args[1]} does not exist in dataset.")
        order = "DESC" if str(args[0]).startswith("top") else "ASC"
        entry = f""" 
        SELECT Entity, Year, {data} 
        FROM {type} 
        WHERE Year = :year 
        ORDER BY {data} {order[args[0]]} 
        LIMIT :n """
        vals = self.db.query(entry, year=args[1], n=args[2]).all(as_dict=True)
        return vals

    def query_range(self, type: str, data: str, args: list) -> list:
        """
        Search entity data in set of two given years.
        Parameters:
            type (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) != 3:
            raise ValueError("Invalid argument.")
        vals = [self.query_regions(type, data, [args[0], i]) for i in [args[1], args[2]]]
        return vals[0] + vals[1]
        
    def query_list(self, type: str, args: list) -> list:
        """
        List entities in set of given year.
        Parameters:
            type (str): data to query
            args (list): user input
        """
        if len(args) != 1:
            raise ValueError("Invalid argument.")
        vals = self.db.query(f"SELECT Entity, Year, FROM {type}").all(as_dict=True)
        if any(r["Year"] == args[0] for r in vals):
            return [r for r in vals if r["Year"] == args[0]]
        raise ValueError(f"Year {args[0]} does not exist in dataset.")
    
    def query_aggregator(self, type: str, data: str, args: list) -> list:
        """
        Search data for entities in set of given year.
        Parameters:
            type (str): data to query
            data (str): columns to filter
            args (list): user input
        """
        if len(args) < 2:
            raise ValueError("Invalid argument.")
        vals = self.db.query(f"SELECT Entity, Year, {data} FROM {type}").all(as_dict=True)
        if any(r["Year"] == args[-1] for r in vals):
            for i in args[0:-1]:
                if not any(r["Entity"] == i for r in vals):
                    raise ValueError(f"Entity {i} does not exist in dataset.")
                if not any(r["Entity"] == i and r["Year"] == args[-1] for r in vals):
                    raise ValueError(f"Entity {i} does not exist for {args[-1]}.")
            return [r for r in vals if r["Year"] == args[-1] and r["Entity"] in args[:-1]]
        raise ValueError(f"Year {args[-1]} does not exist in dataset.")