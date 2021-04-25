import hy
import hy.macros

def _read_exprs(buffer):
    "Evaluate all expressions of buffer"
    results = []
    while buffer:
        try:
            results.append(hy.eval(hy.read(buffer)))
        except EOFError:
            return filter(bool, results)

def read_definitions(config_path):
    """Import macros for reading definitions and parse definitions at provided path

    Each evaluation is expected to be a tuple in order to fill a dictionary
    Then the first element of the tuple must be hashable.
    """
    hy.macros.require("sunflower.utils.macros", None, "ALL")
    with open(config_path) as f:
        return dict(_read_exprs(f))
