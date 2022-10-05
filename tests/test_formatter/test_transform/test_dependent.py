import pytest

from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.dependent import DependentTransform
from ice.formatter.transform.dependent import plural_transform


@pytest.mark.parametrize(("case", "expected"), (((1, 2, 3), "are"), (1, "is")))
def test_plural_transform(case, expected):
    xform = plural_transform("key", singular_case="is", plural_case="are")
    assert isinstance(xform, DependentTransform)
    assert xform.key() == "key"
    assert xform.transform(case) == expected


def test_count_word():
    xform = CountWord("key", special={4: "yay four"})
    for case, expected in (
        (1, "one"),
        (["hi", "hello"], "two"),
        (3, "three"),
        ((0, 0, 0, 0), "yay four"),
    ):
        assert xform.transform(case) == expected  # type: ignore[arg-type]
