import dataclasses
from inspect import isfunction
from math import isnan
from typing import Any
from typing import Union

from fvalues import F


JSONValue = Union[
    str, int, float, bool, None, list["JSONValue"], dict[str, "JSONValue"]
]


def to_json_value(x: Any) -> JSONValue:
    if isinstance(x, dict):
        return {
            k if isinstance(k, str) else repr(k): to_json_value(v) for k, v in x.items()
        }
    if isinstance(x, (list, tuple, set)):
        return [to_json_value(v) for v in x]
    if isinstance(x, F):
        return {"__fstring__": to_json_value(x.parts)}
    if hasattr(x, "dict") and callable(x.dict):
        try:
            x = x.dict()
        except TypeError:  # raised if wrong number of arguments
            pass
        else:
            return to_json_value(x)
    if dataclasses.is_dataclass(x):
        return to_json_value(dataclasses.asdict(x))
    if isfunction(x):
        return dict(class_name=x.__class__.__name__, name=x.__name__)
    if isinstance(x, float):
        return None if isnan(x) else x
    if isinstance(x, (int, str, bool, type(None))):
        return x
    return repr(x)
