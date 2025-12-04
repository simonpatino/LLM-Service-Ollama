from fastapi import FastAPI
import httpx
from pydantic import BaseModel
from fastapi import APIRouter, HTTPExceptionm, Depends
from api.models.user import ChatRequest
from api.core.security import get_current_user
router = APIRouter(tags=["chat"])


OLLAMA_URL = "http://ollama:11434/api/generate"




@router.post("/chat", response_model=dict)
async def chat(request: ChatRequest, current_user=Depends(get_current_user)) -> dict:
    payload = {
        "model": "llama3",
        "prompt": request.prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=200) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        data = response.json()

        return {"response": data.get("response", "")}
