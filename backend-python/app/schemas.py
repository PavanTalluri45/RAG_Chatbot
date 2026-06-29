from typing import List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request."""

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User question",
    )


class Source(BaseModel):
    """Source metadata returned by the RAG system."""

    section: str
    heading: str


class Timing(BaseModel):
    """Performance timings."""

    cache_hit: bool = False
    validation_time: float = 0.0
    embedding_time: float = 0.0
    retrieval_time: float = 0.0
    prompt_build_time: float = 0.0
    gemini_time: float = 0.0
    total_time: float = 0.0


class ChatResponse(BaseModel):
    """Chatbot response."""

    question: str
    answer: str
    sources: List[Source]
    timing: Timing


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    chroma: bool
    redis: bool
    llm: bool