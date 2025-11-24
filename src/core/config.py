import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class PrefixConfig(BaseModel):
    api_v1: str = "/api/v1"
    users: str = "/users"
    auth: str = "/auth"


class DatabaseConfig(BaseModel):
    url: str
    test_db_url: str
    echo: bool = True
    echo_pool: bool = True


class AuthJWTConfig(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire: int = 60 * 3  # seconds * minutes
    refresh_token_expire: int = 60 * 60 * 24 * 14  # seconds * minutes * hours * days


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    prefix: PrefixConfig = PrefixConfig()
    db: DatabaseConfig
    jwt: AuthJWTConfig


settings = Settings()