import inspect
import sys

from ProductionCode.datasource import DataSource

def process(args: list, ds: DataSource):
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
        val = func[args[0].strip()](args[1:])
        return val
    except KeyError:
        print("CLI: Invalid data parameter. -h for help.")
    except IndexError:
        print("CLI: Insufficient parameters. -h for help.")
    except ValueError as e:
        print(f"CLI: {e} -h for help.")
    except Exception:
        print("Process.")

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
        args = input("CLI: Options are 'func', 'data', 'q'.")
        if args == "q": 
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

def translate(args, vals):
    """
    Print values.
    Parameters:
        args (list): user input
        vals (list): list of dicts
    """
    if args[0] == "range":
        key = list(vals[0].keys())[2]
        val_1 = list(vals[0].values())[2]
        val_2 = list(vals[1].values())[2]
        print("second if")
        print(key, val_1, val_2)
    elif args[0] == "list":
        for i in range(len(vals)):
            print(vals[i]["entity"])
    elif args[0] in ["top-gain", "top-emitters", "lowest-emitters", "lowest-gain"]:
        keys = list(vals[0].keys())
        fir, sec = keys[0], keys[2]
        for i in range(len(vals)):
            print(vals[i][fir] + ":", vals[i][sec])
    elif args[0] == "aggregate":
        keys = list(vals[0].keys())
        fir, sec = keys[0], keys[2]
        for i in range(len(vals)):
            print(vals[i][fir] + ":", vals[i][sec])
    else:
        val = list(vals[0].values())[2]
        key = list(vals[0].keys())[2]
        print("first if")
        print(key + ":", val)

def main():
    ds = DataSource()
    vals = process(sys.argv[1:], ds)
    if vals is not None:
        translate(sys.argv[2:], vals)
    while True:
        args = input("CLI ('q' to exit): ").split()
        if args[0] == "q":
            break
        elif args:
            vals = process(args, ds)
            if vals is not None:
                translate(args[1:], vals)
        else:
            print("Invalid input.")

if __name__ == "__main__":
    main()