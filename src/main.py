import uvicorn
from fastapi import FastAPI

from core.config import settings
from api.router import router as api_router

from utils import model_loader  # noqa: F401

app = FastAPI()

app.include_router(api_router, prefix=settings.prefix.api)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
