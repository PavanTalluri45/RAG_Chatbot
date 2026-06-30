import logging

logger = logging.getLogger(__name__)


def should_retry(exc: Exception) -> bool:
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


def get_meaningful_error_message(exc: Exception) -> str:
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
