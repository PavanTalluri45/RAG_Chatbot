import logging
import time
from typing import Any

from google import genai

from src import prompt_builder, redis_cache, retriever, vector_store
from src.config import (
    GOOGLE_LLM_API_KEY,
    MAX_RETRIES,
    MODEL_NAME,
    PROMPT_CHARACTER_LIMIT,
    TOP_K,
)
from src.intent_detector import IntentDetector
from src.conversation import ConversationHandler
from src.error_handler import should_retry, get_meaningful_error_message

logger = logging.getLogger(__name__)


class RAGChain:
    """
    Execution chain coordinating Redis caching, semantic retrieval,
    prompt validation, intent detection, direct conversation handling,
    and Gemini generation.
    """

    def __init__(self) -> None:
        if not GOOGLE_LLM_API_KEY:
            raise RuntimeError("GOOGLE_LLM_API_KEY not found in configuration.")

        self.client: genai.Client = genai.Client(api_key=GOOGLE_LLM_API_KEY)
        self.intent_detector: IntentDetector = IntentDetector()
        self.conversation_handler: ConversationHandler = ConversationHandler(self.client)
        logger.info("RAGChain initialized successfully.")

    def ask(
        self,
        question: str,
        frontend_start: str | None = None,
        bff_start: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a user question. Routes to either Direct Gemini Conversation
        or RAG pipeline based on intent classification.
        """
        t_start = time.perf_counter()
        fastapi_start_wall = time.time() * 1000
        validation_time = 0.0
        detection_time = 0.0
        gemini_time = 0.0

        if frontend_start:
            try:
                fe_start_val = float(frontend_start)
                logger.info("[PERFORMANCE LOG] Latency from Frontend to FastAPI: %.2f ms", fastapi_start_wall - fe_start_val)
            except Exception:
                pass
        if bff_start:
            try:
                bff_start_val = float(bff_start)
                logger.info("[PERFORMANCE LOG] Latency from BFF to FastAPI: %.2f ms", fastapi_start_wall - bff_start_val)
            except Exception:
                pass

        try:
            # 1. Validation
            t_val_start = time.perf_counter()
            if not question:
                validation_time = time.perf_counter() - t_val_start
                tot_time = time.perf_counter() - t_start
                return {
                    "question": "",
                    "answer": "Question cannot be empty.",
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": tot_time,
                        "validation_time": validation_time,
                        "conversation_detection_time": 0.0,
                        "embedding_time": 0.0,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            question = question.strip()
            if len(question) < 2:
                validation_time = time.perf_counter() - t_val_start
                tot_time = time.perf_counter() - t_start
                return {
                    "question": question,
                    "answer": "Question is too short.",
                    "sources": [],
                    "timing": {
                        "cache_hit": False,
                        "total_time": tot_time,
                        "validation_time": validation_time,
                        "conversation_detection_time": 0.0,
                        "embedding_time": 0.0,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            logger.info("Question: %s", question)
            validation_time = time.perf_counter() - t_val_start

            # 2. Check Answer Cache (both RAG and Conversation)
            t_redis_start = time.perf_counter()
            cached_answer = redis_cache.get_answer_cache(question)
            redis_time = time.perf_counter() - t_redis_start
            logger.info("Redis Answer Cache Check Time: %.2f ms", redis_time * 1000)

            if cached_answer is not None:
                logger.info("Cache HIT")
                total_time = time.perf_counter() - t_start

                print("\n====================================================")
                print("Performance Summary  [CACHE HIT]")
                print(f"Validation        : {validation_time:.2f} sec")
                print(f"Redis Cache Check : {redis_time:.4f} sec")
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
                    "conversation_detection_time": 0.0,
                    "embedding_time": 0.0,
                    "retrieval_time": 0.0,
                    "prompt_build_time": 0.0,
                    "gemini_time": 0.0,
                }
                return response_data

            logger.info("Cache MISS")

            # 3. Intent Detection Check
            t_detect_start = time.perf_counter()
            is_conv = self.intent_detector.is_conversational(question)
            detection_time = time.perf_counter() - t_detect_start

            # 4. Direct Conversation Flow (with Caching)
            if is_conv:
                logger.info("Conversation Mode Detected")
                logger.info("Skipping Embedding")
                logger.info("Skipping Chroma")
                logger.info("Skipping Retriever")

                try:
                    conv_res = self.conversation_handler.generate_response(question)
                    gemini_time = conv_res["gemini_time"]
                    total_time = time.perf_counter() - t_start

                    print("\n====================================================")
                    print("Performance Summary  [CONVERSATION]")
                    print(f"Validation        : {validation_time:.2f} sec")
                    print(f"Conversation Det  : {detection_time:.2f} sec")
                    print(f"Gemini            : {gemini_time:.2f} sec")
                    print(f"Total             : {total_time:.2f} sec")
                    print("====================================================\n")

                    logger.info("Total Time: %.2f sec", total_time)

                    response_data = {
                        "answer": conv_res["answer"],
                        "sources": [],
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "model": MODEL_NAME,
                    }
                    # Save conversational response to Redis Cache
                    redis_cache.set_answer_cache(question, response_data)

                    response_data_with_timing = response_data.copy()
                    response_data_with_timing["question"] = question
                    response_data_with_timing["timing"] = {
                        "cache_hit": False,
                        "total_time": total_time,
                        "validation_time": validation_time,
                        "conversation_detection_time": detection_time,
                        "embedding_time": 0.0,
                        "retrieval_time": 0.0,
                        "prompt_build_time": 0.0,
                        "gemini_time": gemini_time,
                    }
                    return response_data_with_timing
                except Exception as error:
                    logger.exception("Conversation flow failure")
                    total_time = time.perf_counter() - t_start

                    print("\n====================================================")
                    print("Performance Summary  [CONVERSATION ERROR]")
                    print(f"Validation        : {validation_time:.2f} sec")
                    print(f"Conversation Det  : {detection_time:.2f} sec")
                    print(f"Gemini            : {gemini_time:.2f} sec")
                    print(f"Total             : {total_time:.2f} sec")
                    print("====================================================\n")

                    logger.info("Total Time: %.2f sec", total_time)

                    return {
                        "question": question,
                        "answer": get_meaningful_error_message(error),
                        "sources": [],
                        "error": str(error),
                        "timing": {
                            "cache_hit": False,
                            "total_time": total_time,
                            "validation_time": validation_time,
                            "conversation_detection_time": detection_time,
                            "embedding_time": 0.0,
                            "retrieval_time": 0.0,
                            "prompt_build_time": 0.0,
                            "gemini_time": gemini_time,
                        },
                    }

            # 5. Check Embedding Cache
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

            # 6. Retrieval
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
                        "conversation_detection_time": detection_time,
                        "embedding_time": embedding_time,
                        "retrieval_time": retrieval_time,
                        "prompt_build_time": 0.0,
                        "gemini_time": 0.0,
                    },
                }

            # 7. Prompt Construction
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

            # 8. Gemini API Interaction with Exponential Retries
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

                    if attempt < MAX_RETRIES and should_retry(exc):
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

            # 9. Response formatting & caching
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
            print(f"Conversation Det  : {detection_time:.2f} sec")
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
                "conversation_detection_time": detection_time,
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
            _det_time = _locals.get("detection_time", 0.0)
            _emb_time = _locals.get("embedding_time", 0.0)
            _ret_time = _locals.get("retrieval_time", 0.0)
            _prm_time = _locals.get("prompt_build_time", 0.0)
            _gem_time = _locals.get("gemini_time", 0.0)

            print("\n====================================================")
            print("Performance Summary  [ERROR]")
            print(f"Validation        : {_val_time:.2f} sec")
            print(f"Conversation Det  : {_det_time:.2f} sec")
            print(f"Embedding         : {_emb_time:.2f} sec")
            print(f"Retrieval         : {_ret_time:.2f} sec")
            print(f"Prompt            : {_prm_time:.2f} sec")
            print(f"Gemini            : {_gem_time:.2f} sec")
            print(f"Total             : {total_time:.2f} sec")
            print("====================================================\n")

            logger.info("Total Time %.2f sec", total_time)

            return {
                "question": question,
                "answer": get_meaningful_error_message(error),
                "sources": [],
                "error": str(error),
                "timing": {
                    "cache_hit": False,
                    "total_time": total_time,
                    "validation_time": _val_time,
                    "conversation_detection_time": _det_time,
                    "embedding_time": _emb_time,
                    "retrieval_time": _ret_time,
                    "prompt_build_time": _prm_time,
                    "gemini_time": _gem_time,
                },
            }