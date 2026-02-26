"""For docstring functionality."""
import inspect
import sys

from datasource import DataSource

def process(args: list, ds: DataSource):
    """
    Process user input.
    Parameters:
        args (list): user input
        ds (DataSource): query module
    """
    if args[0] == "-h":
        return helper(ds)
    func = {"forest-change": ds.query_forest, "co2": ds.query_co2, "temps": ds.query_temps}
    try:
        args = reader(args, func)
        return func[args[0].strip()](args[1:])
    except IndexError:
        print("CLI: Insufficient parameters. -h for help.")
        return None
    except (ValueError, KeyError) as e:
        print(f"CLI: {e} -h for help.")
        return None

def reader(args: list, func: dict):
    """
    Catch data misinput, parse entity names.
    Parameters:
        args (list): user input
        func (dict): dictionary of functions
        ds (DataSource): query module
    """
    if not args[0] in list(func.keys()):
        raise KeyError("Invalid data parameter.")
    if not args[1] in ["list", "top", "bottom", "aggregate"]:
        i = 2 if args[1] == "range" else 1
        args[i] = args[i].replace('-', ' ')
        return args
    if args[1] == "aggregate":
        for i in range(2, len(args) - 1):
            args[i] = args[i].replace('-', ' ')
        return args
    return args

def helper(ds: DataSource):
    """
    Process help requests.
    Parameters:
        ds (DataSource): query module
    """
    op1 = ["data entity year", ds.query_regions]
    op2 = ["data entity year-1 year-2", ds.query_range]
    op3 = ["data year", ds.query_list]
    op4 = ["data entity-1 entity-2 .. year", ds.query_aggregator]
    op5 = ["data order N year, order: top, bottom", ds.query_order_n]
    ops = {"search": op1, "range": op2, "list": op3, "aggregate": op4, "chart": op5}
    while True:
        args = input("CLI ('func', 'data', 'q'): ")
        if args == "q":
            break
        if args == "func":
            func = input("CLI ('search', 'range', 'list', 'aggregate', 'chart'): ")
            try:
                print(inspect.getdoc(ops[func][1]).split("\n", maxsplit=1)[0])
                print(f"format: {ops[func][0]}")
            except KeyError:
                print("CLI: Invalid key search.")
        elif args == "data":
            print("'forest_change', 'co2', 'temps'")
        else:
            print("CLI: Invalid input.")

def translate(args: list, vals: list):
    """
    Translate dict into values.
    Parameters:
        args (list): user input
        vals (list): list of dicts
    """
    if args[0] == "range":
        key = list(vals[0].keys())[2]
        print(key, *(f"{year}: {list(v.values())[2]}" for year, v in zip(args[2:], vals)), sep="\n")
    elif args[0] == "list":
        print(*(v["entity"] for v in vals), sep="\n")
    elif args[0] in ["top", "bottom", "aggregate"]:
        keys = list(vals[0].keys())
        print(keys[2], *(f"{v[keys[0]]}: {v[keys[2]]}" for v in vals), sep="\n")
        if args[0] == "aggregate":
            print("Sum:", sum(v[keys[2]] for v in vals))
    else:
        print(f"{list(vals[0].keys())[2]}: {list(vals[0].values())[2]}")

def main():
    """Handle user arguments."""
    ds = DataSource()
    try:
        vals = process(sys.argv[1:], ds)
        if isinstance(vals, list):
            translate(sys.argv[2:], vals)
    except IndexError:
        print("CLI: No user input. -h for help.")
    while True:
        try:
            args = input("CLI ('q' or 'exit' to exit): ").split()
            if args[0] in {"q", "exit"}:
                break
            if args:
                vals = process(args, ds)
                if isinstance(vals, list):
                    translate(args[1:], vals)
            else:
                print("Invalid input.")
        except IndexError:
            print("CLI: No user input. -h for help.")

if __name__ == "__main__":
    main()
