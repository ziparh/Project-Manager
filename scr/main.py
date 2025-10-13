import uvicorn
from fastapi import FastAPI

from core.config import settings
from api.v1.router import router as api_router

app = FastAPI()

app.include_router(api_router, prefix=settings.prefix.api_v1, tags=["api"])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
