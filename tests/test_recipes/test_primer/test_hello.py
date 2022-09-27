import pytest

from ice.recipes.primer.hello import say_hello

@pytest.mark.anyio
async def test_hello():
    assert await say_hello() == "Hello world!"
