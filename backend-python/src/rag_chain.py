import logging
import time
from typing import Any

import google.genai.errors
from google import genai

from src import prompt_builder, redis_cache, retriever, vector_store
from src.config import (
    GOOGLE_LLM_API_KEY,
    MAX_RETRIES,
    MODEL_NAME,
    PROMPT_CHARACTER_LIMIT,
    TOP_K,
)

logger = logging.getLogger(__name__)


def _should_retry(exc: Exception) -> bool:
    """
    Determines if an exception represents a transient failure that should be retried.
    Retries ONLY on:
      - HTTP 503 / Service Unavailable
      - Temporary network failure (socket errors, connection resets)
      - Connection timeouts

    Does NOT retry on:
      - 429 / Quota exhausted / Resource exhausted
      - 400 (Bad Request)
      - 401 (Unauthorized)
      - 403 (Forbidden)
      - 404 (Not Found)
      - Invalid API Key or authentication failures
    """
    exc_name = type(exc).__name__
    exc_str = str(exc).lower()

    if any(q in exc_str for q in ["429", "quota", "exhausted", "too many requests"]):
        return False
    if "ratelimit" in exc_name.lower():
        return False

    if any(a in exc_str for a in ["401", "403", "unauthorized", "forbidden", "api key", "invalid key"]):
        return False

    if "400" in exc_str:
        return False
    if "404" in exc_str:
        return False

    if "503" in exc_str:
        return True

    code = getattr(exc, "code", None)
    if code is not None:
        try:
            code_int = int(code)
            if code_int == 503:
                return True
            if code_int in [400, 401, 403, 404, 429]:
                return False
        except (ValueError, TypeError):
            pass

    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    if any(n in exc_name for n in ["Timeout", "Connect", "Network", "Connection", "MaxRetryError"]):
        return True
    if any(n in exc_str for n in ["timeout", "connection", "network"]):
        return True

    return False


def _get_meaningful_error_message(exc: Exception) -> str:
    """
    Returns a human-readable explanation of the permanent or unrecoverable error.
    """
    exc_str = str(exc).lower()
    if any(q in exc_str for q in ["429", "quota", "exhausted", "too many requests"]):
        return "The AI service is temporarily rate-limited / quota exhausted. Please try again later."
    if any(a in exc_str for a in ["401", "403", "unauthorized", "forbidden", "api key", "invalid key"]):
        return "Authentication with the AI service failed. Please check your API key configuration."
    if "503" in exc_str:
        return "The AI service is temporarily unavailable. Please try again later."
    return f"A failure occurred in the AI service: {exc}"


# -------------------------------------------------------------
# Intent Detection Layer for Greetings & Small Talk
# -------------------------------------------------------------
CONVERSATIONAL_INTENTS = {
    "greetings": {
        "phrases": ["hi", "hello", "hey"],
        "response": "Hello! How can I help you with questions about the Employee Handbook today?"
    },
    "good_morning": {
        "phrases": ["good morning"],
        "response": "Good morning! What would you like to know about the Employee Handbook?"
    },
    "good_afternoon": {
        "phrases": ["good afternoon"],
        "response": "Good afternoon! What would you like to know about the Employee Handbook?"
    },
    "good_evening": {
        "phrases": ["good evening"],
        "response": "Good evening! What would you like to know about the Employee Handbook?"
    },
    "how_are_you": {
        "phrases": ["how are you?", "how are you"],
        "response": "I'm doing well, thanks for asking. How can I assist you with the Employee Handbook?"
    },
    "thanks": {
        "phrases": ["thanks", "thank you"],
        "response": "You're welcome! Let me know if you have any questions about the Employee Handbook."
    },
    "farewells": {
        "phrases": ["bye", "goodbye"],
        "response": "Goodbye! Have a great day."
    }
}


def detect_conversational_intent(text: str) -> str | None:
    """
    Detects if the input text matches common greetings, thanks, farewells,
    or casual small talk. Returns the predefined response, or None if RAG is needed.
    """
    normalized = text.strip().lower()
    
    # Strip common trailing punctuation (except question mark which might be part of the phrase)
    while normalized and normalized[-1] in (".", "!", ",", " "):
        normalized = normalized[:-1]
        
    cleaned_without_q = normalized
    while cleaned_without_q and cleaned_without_q[-1] in ("?",):
        cleaned_without_q = cleaned_without_q[:-1]

    for config in CONVERSATIONAL_INTENTS.values():
        for phrase in config["phrases"]:
            phrase_lower = phrase.lower()
            if normalized == phrase_lower or cleaned_without_q == phrase_lower:
                return config["response"]
    return None


class RAGChain:
    """
    Execution chain coordinating Redis caching, semantic retrieval,
    prompt validation, and Gemini generation.
    """

    def __init__(self) -> None:
        if not GOOGLE_LLM_API_KEY:
            raise RuntimeError("GOOGLE_LLM_API_KEY not found in configuration.")

        self.client: genai.Client = genai.Client(api_key=GOOGLE_LLM_API_KEY)
        logger.info("RAGChain initialized successfully.")

    def ask(self, question: str) -> dict[str, Any]:
        """
        Process a user question through the optimized RAG pipeline.
        Check Cache -> Retrieve -> Build Prompt -> LLM -> Cache Response.
        """
        t_start = time.perf_counter()

        try:
            # 1. Validation
            t_val_start = time.perf_counter()
            if not question:
                val_time = time.perf_counter() - t_val_start
                tot_time = time.perf_counter() - t_start
                return {
                    "question": "",
                    "answer": "Question cannot be empty.",
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": tot_time,
                        "validation_time": val_time,
                        "embedding_time": 0.0,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            question = question.strip()
            if len(question) < 2:
                val_time = time.perf_counter() - t_val_start
                tot_time = time.perf_counter() - t_start
                return {
                    "question": question,
                    "answer": "Question is too short.",
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": tot_time,
                        "validation_time": val_time,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            logger.info("Question: %s", question)
            validation_time = time.perf_counter() - t_val_start

            # Intent Detection Check (Conversational intent detection layer before RAG)
            conversational_response = detect_conversational_intent(question)
            if conversational_response is not None:
                logger.info("Conversational intent detected. Skipping RAG pipeline.")
                total_time = time.perf_counter() - t_start
                return {
                    "question": question,
                    "answer": conversational_response,
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": total_time,
                        "validation_time": validation_time,
                        "embedding_time": 0.0,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            # 2. Check Answer Cache
            cached_answer = redis_cache.get_answer_cache(question)
            if cached_answer is not None:
                logger.info("Cache HIT")
                total_time = time.perf_counter() - t_start

                print("\n====================================================")
                print("Performance Summary  [CACHE HIT]")
                print(f"Validation        : {validation_time:.2f} sec")
                print("Embedding         : 0.00 sec (Cached)")
                print("Retrieval         : 0.00 sec (Cached)")
                print("Prompt            : 0.00 sec (Cached)")
                print("Gemini            : 0.00 sec (Cached)")
                print(f"Total             : {total_time:.2f} sec")
                print("====================================================\n")

                logger.info("Total Request %.2f sec", total_time)

                response_data = cached_answer.copy()
                response_data["question"] = question
                response_data["timing"] = {
                    "cache_hit": True,
                    "total_time": total_time,
                    "validation_time": validation_time,
                    "embedding_time": 0.0,
                    "retrieval_time": 0.0,
                    "prompt_build_time": 0.0,
                    "gemini_time": 0.0,
                }
                return response_data

            logger.info("Cache MISS")

            # 3. Check Embedding Cache
            query_embedding = redis_cache.get_embedding_cache(question)
            if query_embedding is not None:
                logger.info("Embedding Cache HIT")
                embedding_time = 0.0
            else:
                logger.info("Embedding Cache MISS")
                t_embed_start = time.perf_counter()
                query_embedding = vector_store.embed_texts([question], task_type="retrieval_query")[0]
                embedding_time = time.perf_counter() - t_embed_start
                redis_cache.set_embedding_cache(question, query_embedding)

            logger.info("Embedding Time %.2f sec", embedding_time)

            # 4. Retrieval
            retrieved_chunks, retrieval_time = retriever.retrieve_context(
                query_embedding=query_embedding,
                top_k=TOP_K,
            )
            logger.info("Retrieval Time %.2f sec", retrieval_time)

            if not retrieved_chunks:
                logger.warning("No chunks retrieved.")
                total_time = time.perf_counter() - t_start
                return {
                    "question": question,
                    "answer": "I could not find relevant information in the handbook.",
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": total_time,
                        "validation_time": validation_time,
                        "embedding_time": embedding_time,
                        "retrieval_time": retrieval_time,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            # 5. Prompt Construction
            t_prompt_start = time.perf_counter()
            prompt = prompt_builder.build_prompt(
                question=question,
                retrieved_chunks=retrieved_chunks,
            )
            prompt_build_time = time.perf_counter() - t_prompt_start
            logger.info("Prompt Build Time %.2f sec", prompt_build_time)

            prompt_chars = len(prompt)
            estimated_tokens = prompt_chars // 4
            logger.info("Prompt Characters: %d", prompt_chars)
            logger.info("Estimated Tokens: %d", estimated_tokens)

            if prompt_chars > PROMPT_CHARACTER_LIMIT:
                logger.warning(
                    "Prompt size (%d characters) exceeds limit of %d characters!",
                    prompt_chars,
                    PROMPT_CHARACTER_LIMIT,
                )

            # 6. Gemini API Interaction with Exponential Retries
            gemini_time = 0.0
            interaction = None
            gemini_error = None

            for attempt in range(MAX_RETRIES + 1):
                t_gemini_start = time.perf_counter()
                try:
                    interaction = self.client.interactions.create(
                        model=MODEL_NAME,
                        input=prompt,
                    )
                    gemini_time += time.perf_counter() - t_gemini_start
                    gemini_error = None
                    break
                except Exception as exc:
                    gemini_time += time.perf_counter() - t_gemini_start
                    gemini_error = exc

                    if attempt < MAX_RETRIES and _should_retry(exc):
                        wait_time = 2 ** attempt
                        logger.warning(
                            "Transient Gemini error: %s. Retrying in %d seconds...",
                            exc,
                            wait_time,
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error("Gemini call failed on attempt %d: %s", attempt + 1, exc)
                        break

            if gemini_error is not None:
                raise gemini_error

            # 7. Response formatting & caching
            answer = interaction.output_text
            if not answer:
                raise RuntimeError("Empty Gemini response.")

            sources = [
                {
                    "section": chunk["metadata"].get("section", ""),
                    "heading": chunk["metadata"].get("heading", ""),
                }
                for chunk in retrieved_chunks
            ]

            logger.info("Gemini Time %.2f sec", gemini_time)

            total_time = time.perf_counter() - t_start
            logger.info("Total Time %.2f sec", total_time)

            print("\n====================================================")
            print("Performance Summary")
            print(f"Validation        : {validation_time:.2f} sec")
            print(f"Embedding         : {embedding_time:.2f} sec")
            print(f"Retrieval         : {retrieval_time:.2f} sec")
            print(f"Prompt            : {prompt_build_time:.2f} sec")
            print(f"Gemini            : {gemini_time:.2f} sec")
            print(f"Total             : {total_time:.2f} sec")
            print("====================================================\n")

            response_data = {
                "answer": answer,
                "sources": sources,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": MODEL_NAME,
            }

            redis_cache.set_answer_cache(question, response_data)

            response_data_with_timing = response_data.copy()
            response_data_with_timing["question"] = question
            response_data_with_timing["timing"] = {
                "cache_hit": False,
                "total_time": total_time,
                "validation_time": validation_time,
                "embedding_time": embedding_time,
                "retrieval_time": retrieval_time,
                "prompt_build_time": prompt_build_time,
                "gemini_time": gemini_time,
            }
            return response_data_with_timing

        except Exception as error:
            logger.exception("Unexpected RAG failure")
            total_time = time.perf_counter() - t_start

            _locals = locals()
            _val_time = _locals.get("validation_time", 0.0)
            _emb_time = _locals.get("embedding_time", 0.0)
            _ret_time = _locals.get("retrieval_time", 0.0)
            _prm_time = _locals.get("prompt_build_time", 0.0)
            _gem_time = _locals.get("gemini_time", 0.0)

            print("\n====================================================")
            print("Performance Summary  [ERROR]")
            print(f"Validation        : {_val_time:.2f} sec")
            print(f"Embedding         : {_emb_time:.2f} sec")
            print(f"Retrieval         : {_ret_time:.2f} sec")
            print(f"Prompt            : {_prm_time:.2f} sec")
            print(f"Gemini            : {_gem_time:.2f} sec")
            print(f"Total             : {total_time:.2f} sec")
            print("====================================================\n")

            logger.info("Total Time %.2f sec", total_time)

            return {
                "question": question,
                "answer": _get_meaningful_error_message(error),
                "sources": [],
                "error": str(error),
                "timing": {
                    "cache_hit": False,
                    "total_time": total_time,
                    "validation_time": _val_time,
                    "embedding_time": _emb_time,
                    "retrieval_time": _ret_time,
                    "prompt_build_time": _prm_time,
                    "gemini_time": _gem_time,
                },
            }