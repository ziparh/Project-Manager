import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock

from modules.users import repository as user_repository, service as user_service
from modules.auth import service as auth_service
from enums.token import TokenType

from tests.factories import DBUserFactory


@pytest.fixture
def user_service_with_mocks():
    mock_user_repo = AsyncMock(spec=user_repository.UserRepository)
    mock_auth_svc = AsyncMock(spec=auth_service.AuthService)

    user_svc = user_service.UserService(mock_user_repo, mock_auth_svc)

    return user_svc, mock_auth_svc, mock_user_repo


@pytest.mark.asyncio
async def test_get_users_me_success(user_service_with_mocks):
    user_svc, mock_auth_svc, _ = user_service_with_mocks
    test_token = "valid.jwt.token"
    expected_user = DBUserFactory.build()

    mock_auth_svc.get_user_from_token.return_value = expected_user

    db_user = await user_svc.get_users_me(token=test_token)

    mock_auth_svc.get_user_from_token.assert_called_once_with(
        token=test_token,
        token_type=TokenType.ACCESS,
    )
    assert db_user == expected_user

@pytest.mark.asyncio
async def test_get_users_me_invalid_token(user_service_with_mocks):
    user_svc, mock_auth_svc, _ = user_service_with_mocks

    mock_auth_svc.get_user_from_token.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token.",
    )

    with pytest.raises(HTTPException) as exc_info:
        await user_svc.get_users_me(token="invalid.jwt.token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED