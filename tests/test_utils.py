import pytest

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
