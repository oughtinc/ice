import dataclasses

from inspect import isfunction
from typing import Any

from fvalues import F


JSONValue = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


def to_json_value(x: Any) -> JSONValue:
    if isinstance(x, dict):
        return {
            k if isinstance(k, str) else repr(k): to_json_value(v) for k, v in x.items()
        }
    if isinstance(x, (list, tuple, set)):
        return [to_json_value(v) for v in x]
    if isinstance(x, F):
        return {"__fstring__": to_json_value(x.flatten().parts)}
    if hasattr(x, "dict") and callable(x.dict):
        try:
            return to_json_value(x.dict())
        except TypeError:
            pass
    if dataclasses.is_dataclass(x):
        return to_json_value(dataclasses.asdict(x))
    if isfunction(x):
        return dict(class_name=x.__class__.__name__, name=x.__name__)
    if isinstance(x, (int, float, str, bool, type(None))):
        return x
    return repr(x)
