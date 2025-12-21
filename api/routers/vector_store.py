from http.client import HTTPException
from api.core.database import get_session
from api.models.history import ChatHistory
from api.models.vector import postDocument, searchQuery
from api.models.user import ChatRequest
from fastapi import APIRouter, Depends
from api.core.security import get_current_user, Users
import faiss
import numpy as np
import httpx
from sqlmodel import Session, select


router = APIRouter(tags=["vector_store"])


URL_OLLAMA_EMBEDDING = "http://ollama:11434/api/embed"
OLLAMA_URL = "http://ollama:11434/api/generate"
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


OLLAMA_URL = "http://ollama:11434/api/generate"

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


@router.post("/ask", response_model=dict)
async def ask_vector_store(
    query: ChatRequest,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    vector = await get_embedding_from_ollama(query.prompt)
    context = vector_db.search(vector, 3)  # Default 3 documents for context

    statement_history = select(ChatHistory).where(
        ChatHistory.user_id == current_user.id
    )

    history = session.exec(statement_history).all()

    conversation_history = ""
    for chat in history:
        conversation_history += f"{chat.prompt}\n{chat.response}\n"

    systemInstruction = "SYSTEM:\nYou are an assistant that answers questions using the provided context only."

    historyPrompt = "CONVERSATION HISTORY:\n" + conversation_history

    contextPrompt = "RETRIEVE CONTEXT:\n" + "\n".join(context) + "\n\n"

    actualPrompt = "USER QUESTION:\n" + query.prompt + "\n\n"

    instructionPrompt = "INSTRUCTIONS:\n -if the context does not contain the answer, respond with 'I don't know'.\n -Provide concise answers.\n\n"

    full_prompt = (
        systemInstruction
        + "\n\n"
        + contextPrompt
        + instructionPrompt
        + historyPrompt
        + actualPrompt
    )

    payload = {
        "model": "llama3",
        "prompt": full_prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=200) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        data = response.json()
        ai_response = data.get("response", "")

        new_chat = ChatHistory(
            user_id=current_user.id, prompt=query.prompt, response=ai_response
        )

        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)

        return {"response": ai_response}
    

@router.post("/clear_history", response_model=dict)
async def clear_history(
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(ChatHistory).where(ChatHistory.user_id == current_user.id)
    history = session.exec(statement).all()

    for chat in history:
        session.delete(chat)

    session.commit()

    return {"message": "Chat history cleared."}


