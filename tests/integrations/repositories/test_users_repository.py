import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users import repository, model

from tests.factories import DBUserFactory


@pytest.mark.integration
async def test_create_success(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    user_input = DBUserFactory.build()

    created_user = await repo.create(user=user_input)

    assert isinstance(created_user.id, int)
    assert created_user.id > 0
    assert created_user.username == user_input.username

    user_in_db = await db_session.get(model.User, created_user.id)

    assert user_in_db is not None
    assert user_in_db.username == user_input.username


@pytest.mark.integration
async def test_update_by_id_success(test_user: model.User, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    update_data = {
        "username": "newusername",
        "email": "new@example.com",
        "hashed_password": "newhashedpassword",
    }

    result = await repo.update_by_id(user_id=test_user.id, update_data=update_data)
    await db_session.commit()

    assert result.id == test_user.id
    assert result.username == "newusername"
    assert result.email == "new@example.com"
    assert result.hashed_password == "newhashedpassword"


@pytest.mark.integration
async def test_update_by_id_partial_success(
    test_user: model.User, db_session: AsyncSession
):
    repo = repository.UserRepository(db_session)
    update_data = {"email": "new@example.com"}

    result = await repo.update_by_id(user_id=test_user.id, update_data=update_data)
    await db_session.commit()

    assert result.id == test_user.id
    assert result.username == test_user.username
    assert result.email == "new@example.com"
    assert result.hashed_password == test_user.hashed_password


@pytest.mark.integration
async def test_delete_by_id_success(test_user: model.User, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    await repo.delete_by_id(test_user.id)
    await db_session.commit()

    result = await db_session.get(model.User, test_user.id)
    assert result is None


@pytest.mark.integration
async def test_get_by_id_found(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_by_id(test_user.id)

    assert found_user is not None
    assert found_user.id == test_user.id
    assert found_user.username == test_user.username


@pytest.mark.integration
async def test_get_by_id_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_by_id(-1)

    assert found_user is None


@pytest.mark.integration
async def test_get_by_username_found(test_user, db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_by_username(test_user.username)

    assert found_user is not None
    assert found_user.username == test_user.username


@pytest.mark.integration
async def test_get_by_username_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)
    found_user = await repo.get_by_username("not_exists_username")

    assert found_user is None


@pytest.mark.integration
async def test_get_by_username_or_email_found_username(
    test_user, db_session: AsyncSession
):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_by_username_or_email(
        username=test_user.username, email="some_other_email"
    )

    assert found_user is not None
    assert found_user.username == test_user.username


@pytest.mark.integration
async def test_get_by_username_or_email_found_email(
    test_user, db_session: AsyncSession
):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_by_username_or_email(
        username="some_other_username", email=test_user.email
    )

    assert found_user is not None
    assert found_user.username == test_user.username


@pytest.mark.integration
async def test_by_username_or_email_not_found(db_session: AsyncSession):
    repo = repository.UserRepository(db_session)

    found_user = await repo.get_by_username_or_email(
        username="not_exists_username", email="not_exists_email"
    )

    assert found_user is None
