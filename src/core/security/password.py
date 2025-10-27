import bcrypt


class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_bytes.decode("utf-8")

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
