from fastapi import FastAPI
import httpx
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from api.core.database import create_db_and_tables
from api.routers import auth, chat


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    # Startup: Create database tables
    create_db_and_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LLM Service with Ollama",
    description="A FastAPI service integrating with Ollama for LLM capabilities.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/", response_model=dict, tags=["root"])
def root():
    return {"message": "LLM Service with Ollama is running."}
