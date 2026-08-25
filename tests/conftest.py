import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def api_client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
