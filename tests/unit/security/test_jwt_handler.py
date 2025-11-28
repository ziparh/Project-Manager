import pytest
import time_machine
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from jwt import InvalidTokenError

from core.security.jwt_handler import JWTHandler
from core.config import settings
from enums.token import TokenType


@pytest.mark.unit
@pytest.mark.parametrize(
    "token_type, user_id, expected_lifetime",
    [
        (TokenType.ACCESS, 1234, settings.jwt.access_token_expire),
        (TokenType.REFRESH, 1234, settings.jwt.refresh_token_expire),
    ],
    ids=["access_token_test", "refresh_token_test"],
)
def test_tokens_creation_and_decoding_success(
    token_type: TokenType,
    user_id: int,
    expected_lifetime: int,
):
    fixed_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with time_machine.travel(fixed_dt, tick=False):
        token = JWTHandler.create(
            user_id=user_id,
            token_type=token_type,
        )

        assert isinstance(token, str)
        assert len(token) > 10

        payload = JWTHandler.decode(token)

        assert isinstance(payload, dict)
        assert payload["type"] == token_type.value
        assert payload["sub"] == str(user_id)

        assert payload["iat"] == fixed_dt.timestamp()
        assert payload["exp"] == fixed_dt.timestamp() + expected_lifetime


@pytest.mark.unit
@pytest.mark.parametrize(
    "token_type, expected_lifetime",
    [
        (TokenType.ACCESS, settings.jwt.access_token_expire),
        (TokenType.REFRESH, settings.jwt.refresh_token_expire),
    ],
    ids=["access_token_test", "refresh_token_test"],
)
def test_decoding_expired_tokens(token_type: TokenType, expected_lifetime: int):
    fixed_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with time_machine.travel(fixed_dt, tick=False):
        token = JWTHandler.create(user_id=1234, token_type=token_type)

    future_dt = fixed_dt + timedelta(seconds=expected_lifetime + 1)

    with time_machine.travel(future_dt, tick=False):
        with pytest.raises(InvalidTokenError):
            JWTHandler.decode(token)


def test_decoding_token_wrong_signature():
    token = JWTHandler.create(user_id=1234, token_type=TokenType.ACCESS)

    wrong_token = token + "invalid"

    with pytest.raises(InvalidTokenError):
        JWTHandler.decode(wrong_token)


def test_decoding_invalid_token():
    invalid_token = "invalid.jwt.token"

    with pytest.raises(InvalidTokenError, match="Invalid token:"):
        JWTHandler.decode(invalid_token)


def test_creation_wrong_token_type():
    mock_token_type = MagicMock(spec=TokenType)
    mock_token_type.value = "WRONG_TOKEN_TYPE"

    with pytest.raises(ValueError, match="Invalid token type:"):
        JWTHandler.create(
            user_id=1,
            token_type=mock_token_type,
        )
