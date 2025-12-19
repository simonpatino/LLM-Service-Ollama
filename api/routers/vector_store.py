from http.client import HTTPException
from api.models.vector import postDocument, searchQuery
from fastapi import APIRouter, Depends
from api.core.security import get_current_user, Users
import faiss
import numpy as np
import httpx


router = APIRouter(tags=["vector_store"])


URL_OLLAMA_EMBEDDING = "http://ollama:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_DIMENSION = 768


class FAISSStore:
    def __init__(self):
        self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        self.documents = []

    def add(self, embedding: list[float], text: str):
        vector = np.array([embedding]).astype("float32")
        self.index.add(vector)
        self.documents.append(text)

    def search(self, query_vector: list[float], k: int):
        vector = np.array([query_vector]).astype("float32")
        _, I = self.index.search(vector, k)
        result = []

        for idx in I[0]:
            if idx != -1:
                result.append(self.documents[idx])
        return result


vector_db = FAISSStore()


async def get_embedding_from_ollama(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30) as client:
        payload = {"model": EMBEDDING_MODEL, "input": text}
        response = await client.post(URL_OLLAMA_EMBEDDING, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ollama embedding failed")

        data = response.json()
        embedding = data.get("embeddings", [])
        if not embedding:
            raise HTTPException(status_code=500, detail="No embedding returned")

        return embedding[0]


@router.post("/document", response_model=dict)
async def add_text(
    text: postDocument, current_user: Users = Depends(get_current_user)
) -> dict:
    vector = await get_embedding_from_ollama(text.text)
    vector_db.add(vector, text.text)
    return {
        "message": "Text added to vector store.",
        "total_docs": len(vector_db.documents),
    }


@router.post("/search")
async def search(
    query: searchQuery, current_user: Users = Depends(get_current_user)
) -> dict:
    vector = await get_embedding_from_ollama(query.text)
    results = vector_db.search(vector, query.k)
    return {"query": query.text, "results": results}
