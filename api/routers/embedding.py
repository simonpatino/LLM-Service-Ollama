from fastapi import APIRouter, Depends
import httpx
from api.models.embed import EmbeddingRequest
from api.models.user import Users
from api.core.security import get_current_user

URL_OLLAMA_EMBEDDING = "http://ollama:11434/api/embed"


router = APIRouter(tags=["embedding"])


@router.post("/embedding", response_model=dict)
async def get_embedding(
    embedding_request: EmbeddingRequest, current_user: Users = Depends(get_current_user)
) -> dict:
    payload = {
        "model": "nomic-embed-text",
        "input": embedding_request.text,
    }

    async with httpx.AsyncClient(timeout=100) as client:
        response = await client.post(URL_OLLAMA_EMBEDDING, json=payload)
        data = response.json()

        return {"vector_length": len(data.get("embeddings", [])[0])
                , "embeddings": data.get("embeddings", [])}

