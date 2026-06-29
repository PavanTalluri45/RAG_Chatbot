import logging
import time
from typing import Any

from src.config import TOP_K
from src.vector_store import get_chroma_client, get_collection_count, get_or_create_collection

logger = logging.getLogger(__name__)


def retrieve_context(
    query_embedding: list[float],
    top_k: int = TOP_K,
) -> tuple[list[dict[str, Any]], float]:
    """
    Query Chroma Cloud collection using a pre-computed query embedding.
    Does not perform any sibling injection, neighbor retrieval, or secondary query.

    Parameters
    ----------
    query_embedding : list[float]
        The embedding vector for the question.
    top_k : int
        Number of matches to retrieve.

    Returns
    -------
    tuple[list[dict[str, Any]], float]
        List of retrieved chunk dicts (id, document, metadata, distance)
        and the query execution time in seconds.
    """
    if not query_embedding:
        raise ValueError("Query embedding cannot be empty.")

    client = get_chroma_client()
    if client is None:
        raise RuntimeError("Failed to create Chroma client.")

    collection = get_or_create_collection(client)
    collection_size = get_collection_count()
    if collection_size == 0:
        raise RuntimeError("Collection is empty.")

    t_search_start = time.perf_counter()
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results: list[dict[str, Any]] = []
    if raw and raw.get("ids") and len(raw["ids"]) > 0:
        for i, doc_id in enumerate(raw["ids"][0]):
            results.append(
                {
                    "id": doc_id,
                    "document": raw["documents"][0][i],
                    "metadata": raw["metadatas"][0][i],
                    "distance": raw["distances"][0][i],
                }
            )
    search_time = time.perf_counter() - t_search_start
    logger.info("Retrieved %d chunks", len(results))

    return results, search_time