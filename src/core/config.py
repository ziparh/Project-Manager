from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./database.db"
    echo: bool = True
    echo_pool: bool = True


class PrefixConfig(BaseModel):
    api_v1: str = "/api/v1"
    users: str = "/users"
    auth: str = "/auth"


class AuthJWTConfig(BaseModel):
    algorithm: str = "HS256"
    secret_key: str = "secret"
    access_token_expire: int = 60 * 3  # seconds * minutes
    refresh_token_expire: int = 60 * 60 * 24 * 14  # seconds * minutes * hours * days


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    db: DatabaseConfig = DatabaseConfig()
    prefix: PrefixConfig = PrefixConfig()
    jwt: AuthJWTConfig = AuthJWTConfig()


settings = Settings()
