from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models, service  # noqa: F401 - ensures tables are registered
from app.database import SessionDependency, init_db
from app.exception_handlers import register_exception_handlers
from app.routers.auth import auth_router
from app.routers.post import post_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          # runs on startup
    yield                    # app runs here
    # (anything after yield runs on shutdown)

app = FastAPI(title="Blog API", lifespan=lifespan)
app.include_router(router=post_router)
app.include_router(router=auth_router)
register_exception_handlers(app)


@app.get("/health")
async def health(session: SessionDependency, page: int = 1, per_page: int = 1) -> dict[str, str]:
    # added call to test dependencies
    await service.get_all_posts(session=session, page=page, per_page=per_page)

    return {"status": "ok"}