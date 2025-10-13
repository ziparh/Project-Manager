from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RunConfig(BaseModel):
    host: str = '127.0.0.1'
    port: int = 8000
    reload: bool = True


class PrefixConfig(BaseModel):
    api_v1: str = '/api/v1'


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    prefix: PrefixConfig = PrefixConfig()


settings = Settings()
