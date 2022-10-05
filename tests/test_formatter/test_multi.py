import pytest

from structlog.testing import capture_logs

from ice.formatter.multi import _parse
from ice.formatter.multi import _STOP_EARLY_WARNING
from ice.formatter.multi import _unparse
from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.dependent import CountWord
from ice.formatter.transform.positional import OrdinalWord
from ice.formatter.transform.value import non_literal
from ice.formatter.transform.value import numbered_list


def test_parse_and_unparse_are_inverses():
    complex_format_string = "{{This is some {{nested}} nonsense!}}, \
        and {{conversions!r}} and empty {{:2f}} {{}} {{!a:2d}} format \
        strings work as well as unmatched and escaped {{}} \
        }} braces {{ right up until the {{end:.2f}}"
    assert _unparse(_parse(complex_format_string)) == complex_format_string


def test_stop_partial():
    format_str = "We can start {here} and keep going {there}."
    cases = format_multi(
        format_str,
        [dict(here="in Egypt", there="to France"), dict(here=stop("partying."))],
    )
    assert cases == (
        "We can start in Egypt and keep going to France.",
        "We can start partying.",
    )


def test_warn_stop_early():
    format_str = "We can start {here} and keep going {there}."
    with capture_logs() as logs:
        cases = format_multi(
            format_str,
            [
                dict(here=stop("partying."), there="to France"),
                dict(here="in Egypt", there="to France"),
            ],
        )
    events = {logged["event"] for logged in logs}
    assert _STOP_EARLY_WARNING in events
    assert cases == (
        "We can start partying.",
        "We can start in Egypt and keep going to France.",
    )


def test_shared():
    format_str = "{a} and {b}"
    differing = [dict(a="pizza"), dict(a="hotdogs")]
    shared = dict(b="fries")
    cases = format_multi(format_str, differing, shared)
    assert cases == ("pizza and fries", "hotdogs and fries")

    overriding_case = [dict(a="pizza", b="ice cream")]
    overriden = format_multi(format_str, overriding_case, shared)[0]
    assert overriden == "pizza and ice cream"


def test_apply_transforms():
    format_str = "{a} {b}"
    special = [1, 2, 3]
    with pytest.raises(KeyError):
        format_multi(format_str, [dict(a=non_literal(special))])

    special_count = CountWord("a")

    filled = format_multi(format_str, [dict(a=non_literal(special), b=special_count)])[
        0
    ]
    assert filled == f"{special} three"

    filled_numbered_list = format_multi(
        format_str,
        [
            dict(
                a=numbered_list([str(val) for val in special], separator="..."),
                b=special_count,
            )
        ],
    )[0]
    assert filled_numbered_list == "1. 1...2. 2...3. 3 three"

    filled_positions = format_multi(
        format_str, [dict(b="this"), dict(b="that")], dict(a=OrdinalWord())
    )
    assert filled_positions == ("first this", "second that")
