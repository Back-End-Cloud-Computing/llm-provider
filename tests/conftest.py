import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.security import CurrentUser, get_current_user

FAKE_USER = CurrentUser(id="11111111-1111-1111-1111-111111111111", email="teste@ganjj.com", role="CLIENTE")

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
    """Authenticated API client: overrides `get_current_user` so existing
    tests don't need to carry a real token. Auth enforcement itself is
    covered separately in `tests/integration/test_auth.py`, against the
    real dependency."""
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_current_user, None)
