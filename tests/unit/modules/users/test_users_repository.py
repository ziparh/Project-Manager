import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users import repository, model

from tests.factories import DBUserFactory


@pytest.mark.unit
async def test_create_user_success(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user_input = DBUserFactory.build()

    created_user = await repo.create_user(user=user_input)

    assert isinstance(created_user.id, int)
    assert created_user.id > 0
    assert created_user.username == user_input.username

    user_in_db = await db_session.get(model.User, created_user.id)

    assert user_in_db is not None
    assert user_in_db.username == user_input.username


@pytest.mark.unit
async def test_create_user_conflict_username(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user = DBUserFactory.build(username=test_user.username)

    with pytest.raises(IntegrityError):
        await repo.create_user(user=user)


@pytest.mark.unit
async def test_create_user_conflict_email(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user = DBUserFactory.build(email=test_user.email)

    with pytest.raises(IntegrityError):
        await repo.create_user(user=user)


@pytest.mark.unit
async def test_get_user_by_id_found(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_user_by_id(test_user.id)

    assert found_user is not None
    assert found_user.id == test_user.id
    assert found_user.username == test_user.username


@pytest.mark.unit
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_user_by_id(-1)

    assert found_user is None


@pytest.mark.unit
async def test_get_user_by_username_found(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_user_by_username(test_user.username)

    assert found_user is not None
    assert found_user.username == test_user.username


@pytest.mark.unit
async def test_get_user_by_username_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_user_by_username("not_exists_username")

    assert found_user is None


@pytest.mark.unit
async def test_get_user_by_username_or_email_found_username(
        test_user,
        db_session: AsyncSession
):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_user_by_username_or_email(
        username=test_user.username,
        email="some_other_email"
    )

    assert found_user is not None
    assert found_user.username == test_user.username


@pytest.mark.unit
async def test_get_user_by_username_or_email_found_email(
        test_user,
        db_session: AsyncSession
):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_user_by_username_or_email(
        username="some_other_username",
        email=test_user.email
    )

    assert found_user is not None
    assert found_user.username == test_user.username

@pytest.mark.unit
async def test_user_by_username_or_email_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_user_by_username_or_email(
        username="not_exists_username",
        email="not_exists_email"
    )

    assert found_user is None