from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    """Schema for embedding request."""

    text: str
