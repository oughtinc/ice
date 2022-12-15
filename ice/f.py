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
        if parts is not None:
            expected = "".join(
                part.formatted if isinstance(part, FValue) else part for part in parts
            )
            assert s == expected, f"{s!r} != {expected!r}"
            result = super().__new__(cls, s)
            result.parts = parts
            return result

        frame = inspect.currentframe().f_back
        ex = executing.Source.executing(frame)
        if ex.node is None:
            warnings.warn("Couldn't get source node of F() call")
            return F(s, [s])

        assert isinstance(ex.node, ast.Call)
        [arg] = ex.node.args
        return F(s, F._parts_from_node(arg, frame, s))

    @staticmethod
    def _parts_from_node(node: ast.expr, frame, value) -> list[str | FValue]:
        if isinstance(node, ast.Constant):
            assert isinstance(node.value, str)
            return [node.value]
        if isinstance(node, ast.JoinedStr):
            parts = []
            for node in node.values:
                parts.extend(F._parts_from_node(node, frame, None))
            return parts
        if isinstance(node, ast.FormattedValue):
            n: ast.expr = node.value
            source = ast.unparse(n)
            # TODO cache compiled code?
            value = eval(source, frame.f_globals, frame.f_locals)
            expr = ast.Expression(ast.JoinedStr(values=[node]))
            ast.fix_missing_locations(expr)  # noqa
            # TODO this evals the value again just for the sake of a formatted value
            code = compile(expr, "<ast>", "eval")  # noqa
            formatted = eval(code, frame.f_globals, frame.f_locals)
            return [FValue(source, value, formatted)]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = F._parts_from_node(node.left, frame, value)
            right = F._parts_from_node(node.right, frame, value)
            return left + right
        if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
            left = F._parts_from_node(node.target, frame, value)
            right = F._parts_from_node(node.value, frame, value)
            return left + right
        assert isinstance(value, str)
        return [FValue(ast.unparse(node), value, value)]

    def __deepcopy__(self, memodict=None):
        return F(str(self), deepcopy(self.parts, memodict))

    def dict(self):
        return {"__fstring__": self.flatten().parts}

    def flatten(self):
        parts = []
        for part in self.parts:
            if isinstance(part, FValue) and isinstance(part.value, F):
                parts.extend(part.value.flatten().parts)
            elif isinstance(part, F):
                parts.extend(part.flatten().parts)
            else:
                parts.append(part)
        return F(str(self), parts)

    def strip(self, *args):
        return self.lstrip(*args).rstrip(*args)

    def lstrip(self, *args):
        return self._strip(0, "lstrip", *args)

    def rstrip(self, *args):
        return self._strip(-1, "rstrip", *args)

    def _strip(self, index, method, *args):
        parts = list(self.parts)
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

    def _add(self, other, is_left: bool):
        parts = [self, other] if is_left else [other, self]
        value = str(parts[0]) + str(parts[1])
        frame = inspect.currentframe().f_back.f_back
        node = executing.Source.executing(frame).node
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(
            node.op, ast.Add
        ):
            if isinstance(node, ast.AugAssign):
                left_node = node.target
                right_node = node.value
            else:
                left_node = node.left
                right_node = node.right
            left_parts = F._parts_from_node(left_node, frame, parts[0])
            right_parts = F._parts_from_node(right_node, frame, parts[1])
            parts = left_parts + right_parts

        return F(value, parts)

    def __add__(self, other):
        return self._add(other, True)

    def __radd__(self, other):
        return self._add(other, False)
