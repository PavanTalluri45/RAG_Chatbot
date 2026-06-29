import json
import logging
import time
from typing import Any

from upstash_redis import Redis

from src.config import (
    CACHE_PREFIX,
    DOCUMENT_VERSION,
    REDIS_CACHE_TTL,
    UPSTASH_REDIS_REST_TOKEN,
    UPSTASH_REDIS_REST_URL,
)

logger = logging.getLogger(__name__)

# Singleton client reference
_REDIS_CLIENT: Redis | None = None


def init_redis() -> None:
    """
    Initialize and validate the singleton Upstash Redis client.
    Fails fast if connection is invalid or environment variables are missing.
    """
    global _REDIS_CLIENT

    if _REDIS_CLIENT is not None:
        return

    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_URL.strip():
        raise EnvironmentError(
            "Connection Validation Failed: Environment variable 'UPSTASH_REDIS_REST_URL' "
            "is not set or is empty. Failing fast at startup."
        )
    if not UPSTASH_REDIS_REST_TOKEN or not UPSTASH_REDIS_REST_TOKEN.strip():
        raise EnvironmentError(
            "Connection Validation Failed: Environment variable 'UPSTASH_REDIS_REST_TOKEN' "
            "is not set or is empty. Failing fast at startup."
        )

    try:
        _REDIS_CLIENT = Redis(
            url=UPSTASH_REDIS_REST_URL,
            token=UPSTASH_REDIS_REST_TOKEN,
        )
        # Validate connection with a lightweight GET operation
        _REDIS_CLIENT.get("ping_connection_test")
        logger.info("Redis Connected")
    except Exception as exc:
        logger.exception("Failed to connect to Upstash Redis during startup validation.")
        raise exc


# Fail fast on import
try:
    init_redis()
except Exception as exc:
    logger.exception("Upstash Redis initialization failed.")
    raise exc


def get_redis_client() -> Redis:
    """
    Returns the cached global singleton Upstash Redis client.
    """
    if _REDIS_CLIENT is None:
        init_redis()
    assert _REDIS_CLIENT is not None
    return _REDIS_CLIENT


def normalize_question(question: str) -> str:
    """
    Normalize user questions to stripped lowercase to guarantee cache consistency.
    """
    return question.strip().lower()


def get_answer_cache(question: str) -> dict[str, Any] | None:
    """
    Fetch cached RAG answer from Redis.
    Key format: rag:answer:{DOCUMENT_VERSION}:{normalized_question}
    """
    client = get_redis_client()
    normalized = normalize_question(question)
    key = f"{CACHE_PREFIX}:answer:{DOCUMENT_VERSION}:{normalized}"
    try:
        val = client.get(key)
        if val is not None:
            logger.info("Redis Cache HIT")
            if isinstance(val, str):
                return json.loads(val)
            return val
        logger.info("Redis Cache MISS")
        return None
    except Exception as exc:
        logger.error("Failed to read answer cache from Redis: %s", exc)
        return None


def set_answer_cache(question: str, response_dict: dict[str, Any]) -> None:
    """
    Write completed RAG answer response to Redis with configured TTL.
    Key format: rag:answer:{DOCUMENT_VERSION}:{normalized_question}
    """
    client = get_redis_client()
    normalized = normalize_question(question)
    key = f"{CACHE_PREFIX}:answer:{DOCUMENT_VERSION}:{normalized}"
    try:
        cache_data = {
            "answer": response_dict.get("answer", ""),
            "sources": response_dict.get("sources", []),
            "created_at": response_dict.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": response_dict.get("model") or "gemini-3.1-flash-lite",
        }
        client.set(key, json.dumps(cache_data), ex=REDIS_CACHE_TTL)
    except Exception as exc:
        logger.error("Failed to write answer cache to Redis: %s", exc)


def get_embedding_cache(question: str) -> list[float] | None:
    """
    Fetch cached query embedding from Redis.
    Key format: rag:embedding:{DOCUMENT_VERSION}:{normalized_question}
    """
    client = get_redis_client()
    normalized = normalize_question(question)
    key = f"{CACHE_PREFIX}:embedding:{DOCUMENT_VERSION}:{normalized}"
    try:
        val = client.get(key)
        if val is not None:
            logger.info("Embedding Cache HIT")
            if isinstance(val, str):
                return json.loads(val)
            return val
        logger.info("Embedding Cache MISS")
        return None
    except Exception as exc:
        logger.error("Failed to read embedding cache from Redis: %s", exc)
        return None


def set_embedding_cache(question: str, embedding_vector: list[float]) -> None:
    """
    Write query embedding to Redis with configured TTL.
    Key format: rag:embedding:{DOCUMENT_VERSION}:{normalized_question}
    """
    client = get_redis_client()
    normalized = normalize_question(question)
    key = f"{CACHE_PREFIX}:embedding:{DOCUMENT_VERSION}:{normalized}"
    try:
        client.set(key, json.dumps(embedding_vector), ex=REDIS_CACHE_TTL)
    except Exception as exc:
        logger.error("Failed to write embedding cache to Redis: %s", exc)