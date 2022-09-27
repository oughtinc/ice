import pytest

from ice.recipes.primer.qa_simple import answer


@pytest.mark.anyio
async def test_answer():
    assert await answer() == "I do not know."
