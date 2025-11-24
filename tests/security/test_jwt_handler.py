import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from core.security.jwt_handler import JWTHandler
from core.config import settings
from enums.token import TokenType



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
    time_before_creation = datetime.now(timezone.utc).timestamp() - 0.1

    token = JWTHandler.create(
        user_id=user_id,
        token_type=token_type,
    )

    time_after_creation = datetime.now(timezone.utc).timestamp() + 0.1

    assert isinstance(token, str)
    assert len(token) > 10

    payload = JWTHandler.decode(token)

    assert isinstance(payload, dict)
    assert payload["type"] == token_type.value
    assert payload["sub"] == str(user_id)


    iat = payload["iat"]
    assert iat > time_before_creation
    assert iat < time_after_creation


    exp = payload["exp"]

    expected_ext_low = iat + expected_lifetime - 0.1
    expected_ext_high = iat + expected_lifetime + 0.1

    assert exp > expected_ext_low
    assert exp < expected_ext_high


def test_decoding_invalid_token():
    invalid_token = "invalid.jwt.token"
    result = JWTHandler.decode(invalid_token)

    assert result is None

def test_creation_wrong_token_type():
    mock_token_type = MagicMock(spec=TokenType)
    mock_token_type.value = "WRONG_TOKEN_TYPE"

    with pytest.raises(ValueError, match=f"Invalid token type:"):
        JWTHandler.create(
            user_id=1,
            token_type=mock_token_type,
        ) 