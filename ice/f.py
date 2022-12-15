import ast
import inspect
import warnings
from copy import deepcopy
from dataclasses import dataclass

import executing


@dataclass
class FValue:
    source: str
    value: object
    formatted: str


class F(str):
    def __new__(cls, s, parts=None):
        result = super().__new__(cls, s)
        if parts is not None:
            result.parts = parts
            return result

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

    def __deepcopy__(self, memodict=None):
        return F(str(self), deepcopy(self.parts, memodict))

    def dict(self):
        parts = []
        for part in self.parts:
            if isinstance(part, FValue) and isinstance(part.value, F):
                parts.extend(part.value.parts)
            else:
                parts.append(part)
        return {"__fstring__": parts}

    def strip(self, *args):
        return self.lstrip(*args).rstrip(*args)

    def lstrip(self, *args):
        return self._strip(0, "lstrip", *args)

    def rstrip(self, *args):
        return self._strip(-1, "rstrip", *args)

    def _strip(self, index, method, *args):
        parts = self.parts.copy()
        while True:
            part = parts[index]
            if isinstance(part, FValue):
                s = part.formatted
            else:
                s = part
            s = getattr(s, method)(*args)
            if s:
                if isinstance(part, FValue):
                    part = FValue(part.source, part.value, s)
                else:
                    part = s
                parts[index] = part
                break
            else:
                del parts[index]
        s = getattr(super(), method)(*args)
        return F(s, parts)

    def _add(self, other, method):
        if isinstance(other, F):
            other_parts = other.parts
        elif isinstance(other, str):
            other_parts = [other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: 'F' and '{type(other).__name__}'"
            )
        s = method(str(self), str(other))
        parts = method(self.parts, other_parts)
        return F(s, parts)

    def __add__(self, other):
        return self._add(other, lambda a, b: a + b)

    def __radd__(self, other):
        return self._add(other, lambda a, b: b + a)
