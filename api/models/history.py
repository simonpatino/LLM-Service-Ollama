from datetime import datetime
from sqlmodel import Field, SQLModel


class ChatHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    prompt: str
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
