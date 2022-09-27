import pytest

from ice.recipes.primer.qa import answer


@pytest.mark.anyio
async def test_answer():
    assert await answer() == "A hackathon is happening on 9/9/2022."
