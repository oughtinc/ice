import inspect

import pytest

from ice.utils import get_docstring_from_code
from ice.utils import nsmallest_async


async def cmp(x: int, y: int) -> int:
    return x - y


@pytest.mark.anyio
async def test_nsmallest_async():
    xs = [7, 8, 4, 3, 1, 6, 2, 0, 9, 5]
    assert await nsmallest_async(3, xs, cmp) == [0, 1, 2]
    assert xs == [7, 8, 4, 3, 1, 6, 2, 0, 9, 5]

    assert await nsmallest_async(1, [], cmp) == []
    assert await nsmallest_async(0, [1], cmp) == []
    assert await nsmallest_async(1, [2, 1, 3], cmp) == [1]
    assert await nsmallest_async(-1, [2, 1, 3], cmp) == []
    assert await nsmallest_async(4, [2, 1, 3], cmp) == [1, 2, 3]
    assert await nsmallest_async(1, [1], cmp) == [1]
    assert await nsmallest_async(3, list(range(10)), cmp) == [0, 1, 2]


def test_get_docstring_from_code():
    """distraction..."""

    # fmt: off

    def foo1():
        """
        foo1
            foo2
        """

    def foo2():
        """
    foo2
        foo1
        """

    def foo3():
        """ foo3 foo4 """

    class A:
        """other"""
        @staticmethod
        def foo4():
            """
            foo4
            """

        def foo5(self):
            """ foo5
            6
                7 """

        def foo6(self):
            """
foo6
            """

    # fmt: on

    for func in [foo1, foo2, foo3, A.foo4, A.foo5, A.foo6]:
        assert inspect.getdoc(func).rstrip() == get_docstring_from_code(func.__code__)
