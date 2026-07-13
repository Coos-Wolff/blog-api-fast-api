from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models, service  # noqa: F401 - ensures tables are registered
from app.exception_handlers import register_exception_handlers
from app.routers.auth import auth_router
from app.routers.post import post_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield                    # app runs here
    # (anything after yield runs on shutdown)

app = FastAPI(title="Blog API", lifespan=lifespan)
app.include_router(router=post_router)
app.include_router(router=auth_router)
register_exception_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    # added call to test dependencies
    return {"status": "ok"}