from fastapi import FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from api.core.database import create_db_and_tables
from api.routers import auth, chat, embedding
from api.core.database import engine
from sqlmodel import Session, select


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
app.include_router(embedding.router)


@app.get("/", response_model=dict, tags=["root"])
def root():
    return {"message": "LLM Service with Ollama is running."}


@app.get("/health", response_model=dict, tags=["root"])
def health_check():
    with Session(engine) as session:
        session.exec(select(1)).first()

        if session:
            return {"status": "healthy"}
        else:
            return {"status": "unhealthy"}
