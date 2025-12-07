import pytest
from core.security.password import PasswordHasher


@pytest.mark.unit
class TestCreate:
    def test_valid_hash(self):
        password = "MySuperSecretPassword123"
        hashed = PasswordHasher.hash(password)
        hashed2 = PasswordHasher.hash(password)

        assert isinstance(hashed, str)
        assert isinstance(hashed2, str)

        assert len(hashed) >= 60
        assert len(hashed2) >= 60

        assert password != hashed
        assert hashed != hashed2


@pytest.mark.unit
class TestVerify:
    def test_correct_password(self):
        password = "MyPassword123"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(password, hashed) is True

    def test_incorrect_password(self):
        password = "CorrectPassword123"
        wrong_password = "IncorrectPassword123"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(wrong_password, hashed) is False

    def test_incorrect_hash(self):
        password = "Password321"
        incorrect_hash = "invalid_bcrypt_hash"

        assert PasswordHasher.verify(password, incorrect_hash) is False
