import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users import repository, model

from tests.factories import DBUserFactory


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user_input = DBUserFactory.build()

    created_user = await repo.create_user(user=user_input)

    assert created_user.id is not None
    assert created_user.username == user_input.username

    user_in_db = await db_session.get(model.User, created_user.id)

    assert user_in_db is not None
    assert user_in_db.username == user_input.username


@pytest.mark.asyncio
async def test_create_user_already_exists(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    username = "user"

    user1 = DBUserFactory.build(username=username)
    db_session.add(user1)
    await db_session.commit()

    user2 = DBUserFactory.build(username=username)

    with pytest.raises(IntegrityError):
        await repo.create_user(user=user2)

@pytest.mark.asyncio
async def test_get_user_by_id_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user = DBUserFactory.build()

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    found_user = await repo.get_user_by_id(user.id)

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.username == user.username

@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_user_by_id(-1)

    assert found_user is None

@pytest.mark.asyncio
async def test_get_user_by_username_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user = DBUserFactory.build(username="test_user")

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    found_user = await repo.get_user_by_username("test_user")

    assert found_user is not None
    assert found_user.username == "test_user"

@pytest.mark.asyncio
async def test_get_user_by_username_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_user_by_username("not_exists_username")

    assert found_user is None