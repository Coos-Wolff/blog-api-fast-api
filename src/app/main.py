from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()          # runs on startup
    yield                    # app runs here
    # (anything after yield runs on shutdown)

app = FastAPI(title="Blog API", lifespan=lifespan)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}