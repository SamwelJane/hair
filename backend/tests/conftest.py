import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import _redis_client
from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.main import app


@pytest.fixture(autouse=True)
async def _clean_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        await _redis_client().flushdb()
    except Exception:  # noqa: BLE001, S110 - Redis may not be running locally; rate limiting fails open anyway
        pass
    yield


@pytest.fixture
async def db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
