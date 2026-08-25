import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings

# Tests must never depend on a developer's local `.env` (which may hold a
# real OPENROUTER_API_KEY): disabling dotenv loading here means Settings()
# only ever sees explicit os.environ values and field defaults, so
# monkeypatch.setenv/delenv fully control what each test sees.
Settings.model_config["env_file"] = None


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
