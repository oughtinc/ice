from collections.abc import Mapping
from typing import Optional

from numerizer.consts import ALL_ORDINALS

from ice.formatter.transform import _Transform


class PositionalTransform(_Transform):
    """
    Implement to convert the index of the example to text.
    """

    def transform(self, position: int, total: int) -> str:
        raise NotImplementedError


class OrdinalWord(PositionalTransform):
    """
    Complete with the English ordinal ("first", "second", etc.) up to
    "twentieth", based on the position of the example within the prompt.

    Optionally, special case the last position (e.g., use "finally" or "last" instead
    of an ordinal), and override any other cases by providing a `special` mapping.
    """

    def __init__(
        self,
        capitalize=False,
        finally_case: Optional[str] = None,
        special: Optional[Mapping[int, str]] = None,
    ):
        self.capitalize = capitalize
        self.finally_case = finally_case
        self.words = {(int(v) - 1): k for k, v in ALL_ORDINALS.items()}
        if special:
            for position, word in special.items():
                self.words[position] = word

    def transform(self, position: int, total: int) -> str:
        if position == total - 1 and self.finally_case is not None:
            word = self.finally_case
        else:
            try:
                word = self.words[position]
            except KeyError:
                raise ValueError(f"Position {position} not in ordinal word dictionary")
        return word.capitalize() if self.capitalize else word
