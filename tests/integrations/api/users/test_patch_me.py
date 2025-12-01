import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from modules.users.model import User as UserModel
from modules.users.schemas import UserPatch


@pytest.mark.integration
async def test_patch_me_all_success(
    authenticated_client: AsyncClient,
    test_user: UserModel,
    db_session: AsyncSession,
):
    old_hash = test_user.hashed_password

    update_data = UserPatch(
        username="newusername",
        email="new@example.com",
        password="NewPassword123!",
    )

    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=update_data.model_dump(),
    )
    resp_data = response.json()

    assert response.status_code in (200, 201)
    assert resp_data["id"] == test_user.id
    assert resp_data["username"] == update_data.username
    assert resp_data["email"] == update_data.email
    assert "password" not in resp_data
    assert "hashed_password" not in resp_data

    await db_session.refresh(test_user)

    assert test_user.username == update_data.username
    assert test_user.email == update_data.email
    assert test_user.hashed_password != old_hash


@pytest.mark.integration
@pytest.mark.parametrize(
    "update_data, changed_field",
    [
        (UserPatch(username="newusername"), "username"),
        (UserPatch(email="new@example.com"), "email"),
    ],
)
async def test_patch_me_partial_success(
    authenticated_client: AsyncClient,
    test_user: UserModel,
    db_session: AsyncSession,
    update_data: UserPatch,
    changed_field: str,
):
    update_dict = update_data.model_dump(exclude_unset=True)

    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=update_dict,
    )
    resp_data = response.json()

    assert response.status_code in (200, 201)
    assert resp_data["id"] == test_user.id
    assert resp_data[changed_field] == update_dict[changed_field]

    await db_session.refresh(test_user)

    assert getattr(test_user, changed_field) == update_dict[changed_field]


@pytest.mark.integration
async def test_patch_me_password_success(
    authenticated_client: AsyncClient,
    test_user: UserModel,
    db_session: AsyncSession,
):
    old_hashed_password = test_user.hashed_password
    new_password = "NewPassword123!"

    response = await authenticated_client.patch(
        "api/v1/users/me",
        json={"password": new_password},
    )

    assert response.status_code in (200, 201)

    await db_session.refresh(test_user)

    assert test_user.hashed_password != old_hashed_password
    assert test_user.hashed_password != new_password


@pytest.mark.integration
async def test_patch_me_conflict_username(
    authenticated_client: AsyncClient,
    test_user: UserModel,
):
    update_data = UserPatch(
        username=test_user.username,
        email="new@example.com",
    )

    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=update_data.model_dump(exclude_unset=True),
    )
    resp_data = response.json()

    assert response.status_code == 409
    assert "username already" in resp_data["detail"].lower()


@pytest.mark.integration
async def test_patch_me_conflict_email(
    authenticated_client: AsyncClient,
    test_user: UserModel,
):
    update_data = UserPatch(
        username="newusername",
        email=test_user.email,
    )

    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=update_data.model_dump(exclude_unset=True),
    )
    resp_data = response.json()

    assert response.status_code == 409
    assert "email already" in resp_data["detail"].lower()


@pytest.mark.integration
async def test_patch_me_unexpected_data(
    authenticated_client: AsyncClient,
    test_user: UserModel,
):
    incorrect_data = {"id": 321}
    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=incorrect_data,
    )

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.parametrize(
    "invalid_data, expected_field",
    [
        ({"username": "ab"}, "username"),
        ({"email": "wrong.email@com"}, "email"),
        ({"password": "123"}, "password"),
    ],
)
async def test_patch_me_validator_errors(
    authenticated_client: AsyncClient,
    invalid_data: dict,
    expected_field: str,
):
    response = await authenticated_client.patch(
        "api/v1/users/me",
        json=invalid_data,
    )
    errors = response.json()["detail"]

    assert response.status_code == 422
    assert any(expected_field in str(error["loc"]) for error in errors)
