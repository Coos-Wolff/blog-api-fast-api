import pytest_asyncio
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app import models # noqa F401 - register tables on Base.metadata
from app.base import Base
from app.database import get_db
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest_asyncio.fixture
async def db_setup():
    async with test_engine.begin() as connection:
        await connection.run_sync(lambda c: Base.metadata.create_all(c))
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(lambda c: Base.metadata.drop_all(c))

@pytest_asyncio.fixture
async def session(db_setup):
    test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with test_session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_token(client):
    await client.post("/auth/register", json={
        "email": "jane@example.com", "name": "Jane Doe", "password": "super-strong-password",
    })
    login = await client.post("/auth/login", json={
        "email": "jane@example.com", "password": "super-strong-password",
    })
    return login.json()["access_token"]
