import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from core.security.jwt_handler import JWTHandler
from main import app
from db.base import Base
from db.session import get_session
from modules.users.model import User as UserModel
from core.security.password import PasswordHasher
from core.config import settings
from enums.token import TokenType

from tests.factories import DBUserFactory

from utils import model_loader  # noqa: F401

engine = create_async_engine(
    settings.db.test_db_url,
    poolclass=NullPool,
)

async_test_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            ) as session:
                yield session
                await transaction.rollback()


@pytest.fixture(scope="function")
async def client(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> UserModel:
    user = DBUserFactory.build(
        username="testuser",
        hashed_password=PasswordHasher.hash("TestPassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def access_token(test_user: UserModel) -> str:
    return JWTHandler.create(user_id=test_user.id, token_type=TokenType.ACCESS)

@pytest.fixture
async def refresh_token(test_user: UserModel) -> str:
    return JWTHandler.create(user_id=test_user.id, token_type=TokenType.REFRESH)

@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    access_token: str,
) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client
