from collections.abc import Callable
from collections.abc import Sequence
from typing import Generic
from typing import TypeVar
from typing import Union

from ice.formatter.transform import _Transform


T_contra = TypeVar("T_contra", contravariant=True)


class ValueTransform(_Transform, Generic[T_contra]):
    """
    Implement to functionally transform the value.
    """

    def __init__(
        self, value: T_contra, transform: Callable[[T_contra], Union[str, int]]
    ):
        self.value = value
        self._transform = transform

    def transform(self):
        return self._transform(self.value)


def non_literal(value: T_contra) -> ValueTransform[T_contra]:
    """
    Escape hatch to use a non-literal with `format_multi`
    """
    return ValueTransform(value, transform=lambda v: str(v))


def _paragraphs_to_numbered_list(paragraphs: Sequence[str], separator: str) -> str:
    return separator.join(
        f"{n}. {paragraph}".strip() for n, paragraph in enumerate(paragraphs, 1)
    )


def numbered_list(
    value: Sequence[str], separator: str = "\n"
) -> ValueTransform[Sequence[str]]:
    """Turn a sequence of strings into a single enumerated
    list, beginning with 1.
    """
    return ValueTransform(value, lambda v: _paragraphs_to_numbered_list(v, separator))
