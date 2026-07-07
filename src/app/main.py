from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app import models # noqa: F401 - ensures tables are registered
from app.exception_handlers import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          # runs on startup
    yield                    # app runs here
    # (anything after yield runs on shutdown)

app = FastAPI(title="Blog API", lifespan=lifespan)
register_exception_handlers(app)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}