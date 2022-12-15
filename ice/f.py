import ast
import inspect
import warnings
from dataclasses import dataclass

import executing


@dataclass
class FValue:
    source: str
    value: object
    formatted: str


class F(str):
    def __new__(cls, s):
        result = super().__new__(cls, s)
        frame = inspect.currentframe().f_back
        ex = executing.Source.executing(frame)
        if ex.node is None:
            warnings.warn("Couldn't get source node of F() call")
            result.parts = [s]
            return result

        assert isinstance(ex.node, ast.Call)
        [arg] = ex.node.args
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            result.parts = [s]
            return result

        if not isinstance(arg, ast.JoinedStr):
            raise TypeError(f"F() argument must be an f-string")

        result.parts = []
        for arg in arg.values:
            if isinstance(arg, ast.Constant):
                assert isinstance(arg.value, str)
                result.parts.append(arg.value)
                continue

            assert isinstance(arg, ast.FormattedValue)
            source = ast.unparse(arg.value)
            # TODO cache compiled code?
            value = eval(source, frame.f_globals, frame.f_locals)
            expr = ast.Expression(ast.JoinedStr(values=[arg]))
            ast.fix_missing_locations(expr)  # noqa
            # TODO this evals the value again just for the sake of a formatted value
            code = compile(expr, "<ast>", "eval")  # noqa
            formatted = eval(code, frame.f_globals, frame.f_locals)
            result.parts.append(FValue(source, value, formatted))
        return result

    def dict(self):
        return {"__fstring__": self.parts}
