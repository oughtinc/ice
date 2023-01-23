from collections.abc import Mapping
from collections.abc import Sized
from typing import Generic
from typing import Optional
from typing import TypeVar
from typing import Union

from numerizer.consts import DIRECT_SINGLE_NUMS

from ice.formatter.transform import _Transform


T_contra = TypeVar("T_contra", contravariant=True)


class DependentTransform(_Transform, Generic[T_contra]):
    """
    Implement to complete based on the value of another placeholder.
    """

    def key(self) -> str:
        raise NotImplementedError

    def transform(self, dependent: T_contra) -> str:
        raise NotImplementedError


class CountWord(DependentTransform):
    """
    Fill in based on the value of the placeholder for `key` if it is an integer,
    or else its size.

    By default these will be English counts ("one", "two", "three", etc.), up
    to "twenty". Override or add additional cases by passing in
    a `special` mapping.
    """

    def __init__(self, key: str, special: Optional[Mapping[int, str]] = None):
        self._key = key
        self.words = {int(v): k for k, v in DIRECT_SINGLE_NUMS.items()}
        if special:
            for count, word in special.items():
                self.words[count] = word

    def key(self):
        return self._key

    def transform(self, dependent: Union[int, Sized]) -> str:
        count = dependent if isinstance(dependent, int) else len(dependent)
        try:
            return self.words[count]
        except KeyError:
            raise ValueError(f"Count {count} not in count word dictionary")


def plural_transform(
    key: str, singular_case: str, plural_case: str
) -> DependentTransform[Union[int, Sized]]:
    """
    Return the singular or plural case based on the
    value (if an `int`) or size of the placeholder
    at `key`.
    """

    class SingularOrPlural(DependentTransform):
        def __init__(self, key: str):
            self._key = key

        def key(self):
            return self._key

        def transform(self, dependent: Union[int, Sized]) -> str:
            count = dependent if isinstance(dependent, int) else len(dependent)
            return singular_case if count == 1 else plural_case

    return SingularOrPlural(key)
