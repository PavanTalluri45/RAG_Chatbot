import logging

from fastapi import APIRouter, HTTPException

from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Source,
    Timing,
)
from src.rag_chain import RAGChain

logger = logging.getLogger(__name__)

router = APIRouter()


# -----------------------------------------
# Singleton RAG Instance
# -----------------------------------------

chatbot = RAGChain()


# -----------------------------------------
# Root Endpoint
# -----------------------------------------

@router.get("/")
async def root():
    return {
        "message": "Employee Handbook RAG API",
        "status": "running",
        "version": "1.0.0",
    }


# -----------------------------------------
# Health Endpoint
# -----------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        chroma=True,
        redis=True,
        llm=True,
    )


# -----------------------------------------
# Chat Endpoint
# -----------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):
    try:
        logger.info("Question: %s", request.question)

        result = chatbot.ask(request.question)

        return ChatResponse(
            question=request.question,
            answer=result["answer"],
            sources=[
                Source(
                    section=s["section"],
                    heading=s["heading"],
                )
                for s in result["sources"]
            ],
            timing=Timing(
                cache_hit=result["timing"].get("cache_hit", False),
                validation_time=result["timing"].get("validation_time", 0),
                conversation_detection_time=result["timing"].get("conversation_detection_time", 0),
                embedding_time=result["timing"].get("embedding_time", 0),
                retrieval_time=result["timing"].get("retrieval_time", 0),
                prompt_build_time=result["timing"].get("prompt_build_time", 0),
                gemini_time=result["timing"].get("gemini_time", 0),
                total_time=result["timing"].get("total_time", 0),
            ),
        )

    except Exception as e:
        logger.exception("Chat Endpoint Error")
        raise HTTPException(status_code=500, detail=str(e))