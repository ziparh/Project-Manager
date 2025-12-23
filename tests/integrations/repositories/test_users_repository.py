import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users import repository, model


@pytest.fixture
def repo(db_session: AsyncSession) -> repository.UserRepository:
    return repository.UserRepository(db_session)


@pytest.mark.integration
class TestCreate:
    async def test_success(self, repo, db_session: AsyncSession):
        create_data = {
            "username": "test",
            "email": "test@example.com",
            "hashed_password": "some_hash",
        }
        created_user = await repo.create(data=create_data)

        assert isinstance(created_user.id, int)
        assert created_user.id > 0
        assert created_user.username == create_data["username"]

        user_in_db = await db_session.get(model.User, created_user.id)

        assert user_in_db is not None
        assert user_in_db.username == create_data["username"]


class TestUpdateById:
    async def test_success(self, repo, test_user, db_session: AsyncSession):
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

    async def test_partial_success(
        self, repo, test_user: model.User, db_session: AsyncSession
    ):
        update_data = {"email": "new@example.com"}

        result = await repo.update_by_id(user_id=test_user.id, update_data=update_data)
        await db_session.commit()

        assert result.id == test_user.id
        assert result.username == test_user.username
        assert result.email == "new@example.com"
        assert result.hashed_password == test_user.hashed_password


@pytest.mark.integration
class TestDeleteById:
    async def test_success(self, repo, test_user, db_session: AsyncSession):
        await repo.delete_by_id(test_user.id)
        await db_session.commit()

        result = await db_session.get(model.User, test_user.id)
        assert result is None


@pytest.mark.integration
class TestGetById:
    async def test_found(self, repo, test_user, db_session: AsyncSession):
        found_user = await repo.get_by_id(test_user.id)

        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.username == test_user.username

    async def test_not_found(self, repo, db_session: AsyncSession):
        found_user = await repo.get_by_id(-1)

        assert found_user is None


@pytest.mark.integration
class TestGetByUsername:
    async def test_found(self, repo, test_user, db_session: AsyncSession):
        found_user = await repo.get_by_username(test_user.username)

        assert found_user is not None
        assert found_user.username == test_user.username

    async def test_not_found(self, repo, db_session: AsyncSession):
        found_user = await repo.get_by_username("not_exists_username")

        assert found_user is None


@pytest.mark.integration
class TestGetByUsernameOrEmail:
    async def test_found_username(self, repo, test_user, db_session: AsyncSession):
        found_user = await repo.get_by_username_or_email(
            username=test_user.username, email="some_other_email"
        )

        assert found_user is not None
        assert found_user.username == test_user.username

    async def test_found_email(self, repo, test_user, db_session: AsyncSession):
        found_user = await repo.get_by_username_or_email(
            username="some_other_username", email=test_user.email
        )

        assert found_user is not None
        assert found_user.username == test_user.username

    async def test_not_found(self, repo, db_session: AsyncSession):
        found_user = await repo.get_by_username_or_email(
            username="not_exists_username", email="not_exists_email"
        )

        assert found_user is None
