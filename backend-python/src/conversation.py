import logging
import time
from typing import Any
from google import genai
from src.config import MODEL_NAME, MAX_RETRIES
from src.conversation_prompt import CONVERSATIONAL_SYSTEM_PROMPT
from src.error_handler import should_retry

logger = logging.getLogger(__name__)


class ConversationHandler:
    """
    Handles conversation-mode interactions directly with Gemini,
    skipping embeddings, retriever, database, and caching.
    """

    def __init__(self, client: genai.Client) -> None:
        self.client = client

    def generate_response(self, question: str) -> dict[str, Any]:
        """
        Calls Gemini API with the conversational system prompt.
        Retries on transient errors.
        """
        logger.info("Calling Gemini Conversation Endpoint")
        
        gemini_time = 0.0
        interaction = None
        gemini_error = None

        for attempt in range(MAX_RETRIES + 1):
            t_gemini_start = time.perf_counter()
            try:
                interaction = self.client.interactions.create(
                    model=MODEL_NAME,
                    input=question,
                    system_instruction=CONVERSATIONAL_SYSTEM_PROMPT,
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
                    logger.error("Gemini conversation call failed on attempt %d: %s", attempt + 1, exc)
                    break

        if gemini_error is not None:
            raise gemini_error

        answer = interaction.output_text
        if not answer:
            raise RuntimeError("Empty Gemini response.")

        logger.info("Conversation Response Generated")
        return {
            "answer": answer,
            "gemini_time": gemini_time,
        }
