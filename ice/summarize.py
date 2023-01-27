from dataclasses import dataclass
from typing import Any
from typing import cast
from typing import Optional

from ice.json_value import JSONValue


@dataclass
class Summarizer:
    str_limit: int = 100
    list_limit: int = 3
    dict_limit: int = 10
    depth_limit: int = 4
    float_digits: int = 4

    def summarize(self, x: JSONValue, depth_left: Optional[int] = None):
        if depth_left is None:
            depth_left = self.depth_limit
        elif depth_left <= 0:
            return None
        if isinstance(x, list):
            return self.summarize_list(x, depth_left)
        elif isinstance(x, dict):
            return self.summarize_dict(x, depth_left)
        elif isinstance(x, str):
            return self.summarize_str(x)
        elif isinstance(x, float):
            return self.summarize_float(x)
        else:
            return x

    def summarize_dict(self, x: dict[str, JSONValue], depth_left: int):
        if list(x.keys()) == ["__fstring__"]:
            new_x = {}
            for part in cast(Any, x["__fstring__"]):
                if isinstance(part, dict) and "value" in part:
                    new_x[part["source"]] = part["value"]
            x = new_x

        result = {}
        for k in sorted(x.keys())[: self.dict_limit]:
            v = self.summarize(x[k], depth_left - 1)
            if not self._is_empty(v):
                result[k] = v
        return result

    def summarize_list(self, x: list[JSONValue], depth_left: int):
        result = [self.summarize(v, depth_left - 1) for v in x[: self.list_limit]]
        while result and self._is_empty(result[-1]):
            result.pop()
        return result

    def summarize_str(self, string: str):
        """
        Returns a version of `string` at most `self.str_limit` characters long,
        with the middle replaced by `...` if necessary.
        """
        lim = self.str_limit
        if len(string) > lim:
            # uncomment to omit long strings entirely instead of truncating
            # return None

            middle = "..."
            i = (lim - len(middle)) // 2
            j = lim - len(middle) - i
            string = string[:i] + middle + string[-j:]
        return string

    def summarize_float(self, x: float):
        # TODO use significant digits instead of decimal places?
        return round(x, self.float_digits)

    def _is_empty(self, x: JSONValue):
        return x in ([], {}, "", None)


summarize = Summarizer().summarize
