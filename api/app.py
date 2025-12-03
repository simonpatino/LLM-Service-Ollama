from fastapi import FastAPI
import httpx
from pydantic import BaseModel 
app = FastAPI()

OLLAMA_URL = "http://ollama:11434/api/generate"


class ChatRequest(BaseModel):
    prompt: str


@app.get("/", response_model=dict)
def root():
    return {"messsage": "LLM Service with Ollama is running."}


@app.post("/chat", response_model=dict)
async def chat(request: ChatRequest):
    payload = {
        "model": "llama3",
        "prompt": request.prompt,
        "stream": False
    }

    async with httpx.AsyncClient(timeout= 200) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        data = response.json()

        return {"response": data.get("response", "")}
