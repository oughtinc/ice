import enum
import string
from collections import Counter
from collections.abc import Mapping
from collections.abc import Sequence
from typing import final
from typing import Optional
from typing import Union

from structlog.stdlib import get_logger
from typing_extensions import TypeGuard

from ice.formatter.transform import _Transform
from ice.formatter.transform.dependent import DependentTransform
from ice.formatter.transform.positional import PositionalTransform
from ice.formatter.transform.value import ValueTransform

log = get_logger()

# Tools for building few-shot prompts out of examples

_formatter = string.Formatter()


class _NotNeededSentinel(enum.Enum):
    token = 0


_not_needed_sentinel = _NotNeededSentinel.token


@final
class StopSentinel(str):
    """Stop the string here."""


literal = Union[str, int, float, StopSentinel]

literal_or_transform = Union[literal, _Transform]

FormatValues = Sequence[Mapping[str, literal_or_transform]]

_StdLibFormatStringParses = list[
    tuple[str, Optional[str], Optional[str], Optional[str]]
]


def _is_partial(**fields: Union[literal, _NotNeededSentinel]):
    return any((isinstance(value, StopSentinel) for value in fields.values()))


def all_values_needed(
    examples: Sequence[Mapping[str, Union[literal_or_transform, _NotNeededSentinel]]]
) -> TypeGuard[Sequence[Mapping[str, literal_or_transform]]]:
    return all(
        (
            all(v is not _not_needed_sentinel for v in example.values())
            for example in examples
        )
    )


def _is_keyword_only(parses: _StdLibFormatStringParses) -> bool:
    return all(
        [
            field_name is None or field_name.isidentifier()
            for _, field_name, _, _ in parses
        ]
    )


def _parse(format_placeholder: str) -> _StdLibFormatStringParses:
    parses = list(_formatter.parse(format_placeholder))
    if not _is_keyword_only(parses):
        raise ValueError(
            f"placeholder must use only keyword placeholders: {format_placeholder}"
        )
    return parses


def _literal_brace_escape(literal_text: str) -> str:
    chars = Counter(literal_text)
    # For safety, ensuring these came from string.Formatter.parse
    assert chars.get("{", 0) + chars.get("}", 0) <= 1
    if not literal_text:
        return literal_text
    if literal_text[-1] == "}":
        return "".join((literal_text, "}"))
    if literal_text[-1] == "{":
        return "".join((literal_text, "{"))
    return literal_text


def _unparse(parses: _StdLibFormatStringParses) -> str:
    # Suprisingly this isn't in the stdlib
    parts: list[str] = []
    for literal_text, field_name, format_spec, conversion in parses:
        parts.append(_literal_brace_escape(literal_text))
        if field_name is not None:
            parts.extend(["{", field_name])
            if conversion is not None:
                parts.extend(["!", conversion])
            if format_spec is not None:
                parts.extend([":", format_spec])
            parts.append("}")
    return "".join(parts)


def _no_sentinels_remaining(
    concrete_values: dict[str, Union[literal, _NotNeededSentinel]]
) -> TypeGuard[dict[str, literal]]:
    return all(
        (value is not _not_needed_sentinel for value in concrete_values.values())
    )


def _format_truncate(
    format_placeholder: str,
    /,
    **concrete_values: Union[literal, _NotNeededSentinel],
) -> str:
    if not _is_partial(**concrete_values):
        return format_placeholder
    parses = _parse(format_placeholder)
    keep: _StdLibFormatStringParses = []
    for parse in parses:
        _, field_name, _, _ = parse
        if field_name is None:
            keep.append(parse)
        else:
            keep.append(parse)
            if isinstance(concrete_values[field_name], StopSentinel):
                break
    needed_keys = set(
        (field_name for _, field_name, _, _ in keep if field_name is not None)
    )
    needed_concrete_values = {
        k: v for k, v in concrete_values.items() if k in needed_keys
    }
    if not _no_sentinels_remaining(needed_concrete_values):
        raise ValueError(
            f"Unfilled DependentTransform in partial example:\nFormat: {format_placeholder}\nNeeded Values: {needed_concrete_values}"
        )
    new_str = _unparse(keep).format_map(needed_concrete_values)
    return new_str


def _has_stop(
    concrete_values: Mapping[str, Union[literal, _NotNeededSentinel]]
) -> bool:
    return any(isinstance(value, StopSentinel) for value in concrete_values.values())


def _format_single(
    format_placeholder: str,
    /,
    **concrete_values: Union[literal, _NotNeededSentinel],
) -> tuple[str, bool]:
    if not _has_stop(concrete_values):
        formatted = format_placeholder.format_map(concrete_values)
        truncated = False
    else:
        formatted = _format_truncate(format_placeholder, **concrete_values)
        truncated = True
    return formatted, truncated


def _apply_transforms(
    cases: Sequence[Mapping[str, literal_or_transform]],
    total: int,
) -> Sequence[Mapping[str, Union[literal, _NotNeededSentinel]]]:
    ret_list: list[dict[str, Union[literal, _NotNeededSentinel]]] = []
    for position, case in enumerate(cases):
        ret_dict: dict[str, Union[literal, _NotNeededSentinel]] = {}
        for k, v in case.items():
            if not isinstance(v, _Transform):
                ret_dict[k] = v
            elif isinstance(v, ValueTransform):
                ret_dict[k] = v.transform()
            elif isinstance(v, PositionalTransform):
                ret_dict[k] = v.transform(position, total)
            elif isinstance(v, DependentTransform):
                if v.key() not in case:
                    ret_dict[k] = _not_needed_sentinel
                else:
                    dependent = case[v.key()]
                    ret_dict[k] = (
                        v.transform(dependent.value)
                        if isinstance(dependent, ValueTransform)
                        else v.transform(dependent)
                    )
        ret_list.append(ret_dict)
    return ret_list


_STOP_EARLY_WARNING = "StopSentinel used in non-final case; this may be a mistake."


def _format_multi(
    format_string: str,
    cases: Sequence[Mapping[str, literal_or_transform]],
    strip: bool,
) -> tuple[str, ...]:
    total = len(cases)
    transformed_examples = _apply_transforms(cases, total)
    filled_cases = list(
        map(
            lambda kwargs: _format_single(format_string, **kwargs),
            transformed_examples,
        )
    )
    ret_val, truncated = tuple(c[0].strip() if strip else c[0] for c in filled_cases), [
        c[1] for c in filled_cases
    ]
    if any(truncated[:-1]):
        log.warn(_STOP_EARLY_WARNING, format_string=format_string, cases=cases)
    return ret_val


def stop(value: Union[str, int, float]) -> StopSentinel:
    """Stop here; truncate the rest of the format string."""
    return StopSentinel(value)


def format_multi(
    format_str: str,
    cases: Sequence[Mapping[str, literal_or_transform]],
    shared: Optional[Mapping[str, literal_or_transform]] = None,
    strip: bool = True,
) -> tuple[str, ...]:
    """
    str.Formatter on steroids.

    Repeatedly format a string based on the arguments passed in `cases`.
    Shared arguments belong in `shared`.

    Use Transforms to dynamically change the value based on other values,
    the index of the case, the number of cases, or another function.

    Stop early and truncate a case with a StopSentinel value.
    """
    shared_dict = {k: v for k, v in (shared or dict()).items()}
    return _format_multi(
        format_str, [shared_dict | case for case in cases], strip=strip
    )
