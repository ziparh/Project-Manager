import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.pool import NullPool

from db.base import Base
from core.config import settings

from utils import model_loader  # noqa: F401


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine for the entire test session."""
    engine = create_async_engine(
        settings.db.test_db_url,
        poolclass=NullPool,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional database session for each test.

    Pattern explanation:
    - Connection begins a transaction
    - Session uses that transaction with savepoint support
    - After test, everything is rolled back automatically
    """
    async with test_engine.connect() as connection:
        async with connection.begin() as transaction:
            async with AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as session:
                try:
                    yield session
                finally:
                    await session.rollback()
                    if transaction.is_active:
                        await transaction.rollback()
