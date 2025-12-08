import httpx
from fastapi import APIRouter, Depends
from api.models.user import ChatRequest, Users
from api.core.security import get_current_user
from api.core.database import get_session
from sqlmodel import Session, select
from api.models.history import ChatHistory


router = APIRouter(tags=["chat"])


OLLAMA_URL = "http://ollama:11434/api/generate"


@router.post("/chatTest", response_model=dict)
async def chatTest(
    request: ChatRequest,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    payload = {
        "model": "llama3",
        "prompt": request.prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=200) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        data = response.json()

        return {"response": data.get("response", "")}


@router.post("/chat", response_model=dict)
async def chat(
    request: ChatRequest,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    statement = select(ChatHistory).where(ChatHistory.user_id == current_user.id)
    history = session.exec(statement).all()

    conversation_history = ""
    for chat in history:
        conversation_history += f"{chat.prompt}\n{chat.response}\n"

    full_prompt = conversation_history + request.prompt

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
            user_id=current_user.id, prompt=request.prompt, response=ai_response
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

@router.get("/history", response_model=dict)
async def get_history(
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    statement = select(ChatHistory).where(ChatHistory.user_id == current_user.id)
    history = session.exec(statement).all()
    return {
        "history": [
            {"prompt": chat.prompt, "response": chat.response} for chat in history
        ]
    }





