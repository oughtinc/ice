import os

import pytest

os.environ.update(
    OUGHT_ICE_AUTO_BROWSER="0",
    OUGHT_ICE_AUTO_SERVER="0",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"
