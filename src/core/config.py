from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RunConfig(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8000
    reload: bool = True


class DatabaseConfig(BaseModel):
    url: str = 'sqlite+aiosqlite:///./database.db'
    echo: bool = True
    echo_pool: bool = True

class PrefixConfig(BaseModel):
    api_v1: str = '/api/v1'
    users: str = '/users'


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    db: DatabaseConfig = DatabaseConfig()
    prefix: PrefixConfig = PrefixConfig()


settings = Settings()
