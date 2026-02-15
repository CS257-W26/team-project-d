import inspect
import sys

from ProductionCode.datasource import DataSource

def process(args: list, ds: DataSource) -> list:
    """
    Process user input.
    Parameters:
        args (list): user input
        ds (DataSource): query module
    """
    if args[0] == "-h":
        return help(ds)
    func = {"forest-change": ds.query_forest, "co2": ds.query_co2, "temps": ds.query_temps}
    try:
        return func[args[0]](args[1:])
    except KeyError:
        print("CLI: Invalid data parameter. -h for help.")
    except IndexError:
        print("CLI: Insufficient parameters. -h for help.")
    except ValueError as e:
        print(f"CLI: {e} -h for help.")

def help(ds: DataSource):
    """
    Process help requests.
    Parameters:
        ds (DataSource): query module
    """
    op1 = ["data entity year", ds.query_regions]
    op2 = ["data country year-1 year-2", ds.query_range]
    op3 = ["data year", ds.query_list]
    op4 = ["data entity-1 entity-2 .. year", ds.query_aggregator]
    op5 = ["data order year N", ds.query_order_N]
    ops = {"search": op1, "range": op2, "list": op3, "aggregate": op4, "gain": op5}
    while True:
        args = input("CLI: Options are 'func', 'data', 'quit'.")
        if args == "quit": 
            break
        elif args == "func":
            func = input("CLI: Options are 'search', 'range', 'list', 'aggregate', 'gain'.")
            try:
                print(inspect.getdoc(ops[func][1]).split("\n")[0])
                print(f"format: {ops[func][0]}")
            except KeyError:
                print("CLI: Invalid key search.")
        elif args == "data":
            print("CLI: Options are 'forest_change', 'co2', 'temps'.")
        else:
            print("CLI: Invalid input.")

def translate(vals: list):
    """
    Print values.
    Parameters:
        vals (list): list of dicts
    """
    if len(vals) == 1:
        val = list(vals[0].values())[2]
        key = list(vals[0].keys())[2]
        print(key, val)
    elif len(vals) == 2:
        key = list(vals[0].keys())[2]
        val_1 = list(vals[0].values())[2]
        val_2 = list(vals[1].values())[2]
        print(key, val_1, val_2)
    else:
        print("Something went wrong.")

def main():
    ds = DataSource()
    process(sys.argv[1:], ds)
    while True:
        args = input("CLI ('quit' to exit): ").split()
        if args[0] == "quit":
            break
        elif args:
            vals = process(args)
            translate(vals)
        else:
            print("Invalid input.")

if __name__ == "__main__":
    main()