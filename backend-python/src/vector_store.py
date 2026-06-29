import logging
from typing import Any
import chromadb
from chromadb import CloudClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config import (
    CHROMA_API_KEY,
    CHROMA_DATABASE,
    CHROMA_TENANT,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    GOOGLE_EMBEDDING_API_KEY,
    TOP_K,
    UPSERT_BATCH_SIZE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global Singleton Caches
# ---------------------------------------------------------------------------

_CHROMA_CLIENT: chromadb.ClientAPI | None = None
_CHROMA_COLLECTION: chromadb.Collection | None = None
_DOCUMENT_EMBEDDER: GoogleGenerativeAIEmbeddings | None = None
_QUERY_EMBEDDER: GoogleGenerativeAIEmbeddings | None = None
_COLLECTION_COUNT: int | None = None


def init_singletons() -> None:
    """
    Initialize and cache global Chroma client, collection, and Gemini embedders.
    Validates that all required environment variables are set and connects
    to the vector database immediately to fail fast on startup issues.
    Stores the collection count in memory during startup.
    """
    global _CHROMA_CLIENT, _CHROMA_COLLECTION, _DOCUMENT_EMBEDDER, _QUERY_EMBEDDER, _COLLECTION_COUNT

    required_env_vars = {
        "GOOGLE_EMBEDDING_API_KEY": GOOGLE_EMBEDDING_API_KEY,
        "CHROMA_API_KEY": CHROMA_API_KEY,
        "CHROMA_TENANT": CHROMA_TENANT,
        "CHROMA_DATABASE": CHROMA_DATABASE,
    }

    for name, value in required_env_vars.items():
        if not value or not value.strip():
            raise EnvironmentError(
                f"Connection Validation Failed: Environment variable '{name}' "
                "is not set or is empty in the config. Failing fast at startup."
            )

    if _DOCUMENT_EMBEDDER is None:
        _DOCUMENT_EMBEDDER = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=GOOGLE_EMBEDDING_API_KEY,
            task_type="retrieval_document",
        )
    if _QUERY_EMBEDDER is None:
        _QUERY_EMBEDDER = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=GOOGLE_EMBEDDING_API_KEY,
            task_type="retrieval_query",
        )

    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = CloudClient(
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE,
            api_key=CHROMA_API_KEY,
        )
        logger.info("Chroma Connected")

    if _CHROMA_COLLECTION is None:
        _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Loaded collection %s", COLLECTION_NAME)
        _COLLECTION_COUNT = _CHROMA_COLLECTION.count()


# Fail-fast validation and connection verification during module load
try:
    init_singletons()
except Exception as exc:
    logger.exception("Failed to initialize vector store singletons at startup.")
    raise exc


def _get_embedder(task_type: str = "retrieval_document") -> GoogleGenerativeAIEmbeddings:
    """
    Return a cached singleton GoogleGenerativeAIEmbeddings instance.
    """
    if task_type == "retrieval_query":
        if _QUERY_EMBEDDER is None:
            init_singletons()
        assert _QUERY_EMBEDDER is not None
        return _QUERY_EMBEDDER
    else:
        if _DOCUMENT_EMBEDDER is None:
            init_singletons()
        assert _DOCUMENT_EMBEDDER is not None
        return _DOCUMENT_EMBEDDER


def get_collection_count() -> int:
    """
    Get the cached collection count from memory, loaded during startup.
    """
    global _COLLECTION_COUNT
    if _COLLECTION_COUNT is None:
        client = get_chroma_client()
        collection = get_or_create_collection(client)
        _COLLECTION_COUNT = collection.count()
    return _COLLECTION_COUNT


def embed_texts(
    texts: list[str],
    task_type: str = "retrieval_document",
) -> list[list[float]]:
    """
    Embed an arbitrary number of texts using gemini-embedding-2-preview.
    """
    logger.debug("Embedding %d text(s) with %s …", len(texts), EMBEDDING_MODEL)
    embedder = _get_embedder(task_type=task_type)
    embeddings = embedder.embed_documents(texts)
    logger.debug(
        "Embedding complete (%d vectors, dim=%d).",
        len(embeddings),
        len(embeddings[0]) if embeddings else 0,
    )
    return embeddings


def get_chroma_client() -> chromadb.ClientAPI:
    """
    Return the cached global singleton ChromaDB Cloud client.
    """
    if _CHROMA_CLIENT is None:
        init_singletons()
    assert _CHROMA_CLIENT is not None
    return _CHROMA_CLIENT


def get_or_create_collection(
    client: chromadb.ClientAPI,
    collection_name: str = COLLECTION_NAME,
) -> chromadb.Collection:
    """
    Return the named collection, creating it if it does not yet exist.
    Uses cached global singleton Collection for the default employee handbook.
    """
    global _CHROMA_COLLECTION
    if collection_name == COLLECTION_NAME:
        if _CHROMA_COLLECTION is None:
            init_singletons()
        assert _CHROMA_COLLECTION is not None
        return _CHROMA_COLLECTION
    else:
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )


def upsert_chunks(
    collection: chromadb.Collection,
    chunks: list[dict[str, Any]],
) -> None:
    """
    Embed and upsert a list of chunk dicts into collection.
    """
    if not chunks:
        logger.warning("upsert_chunks called with an empty chunk list – nothing to do.")
        return

    logger.info("Starting upsert of %d chunks …", len(chunks))
    contents = [c["content"] for c in chunks]
    embeddings = embed_texts(contents, task_type="retrieval_document")

    ids: list[str] = []
    metadatas: list[dict[str, str]] = []

    for chunk in chunks:
        doc_id = f"{chunk['source_file']}__chunk_{chunk['chunk_id']}"
        ids.append(doc_id)
        metadatas.append(
            {
                "chunk_id": str(chunk["chunk_id"]),
                "section": chunk.get("section", ""),
                "heading": chunk.get("heading", ""),
                "subheading": chunk.get("subheading", ""),
                "source_file": chunk.get("source_file", ""),
            }
        )

    total = len(chunks)
    for start in range(0, total, UPSERT_BATCH_SIZE):
        end = min(start + UPSERT_BATCH_SIZE, total)
        logger.info("Upserting batch %d–%d / %d …", start + 1, end, total)
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=contents[start:end],
            metadatas=metadatas[start:end],
        )

    global _COLLECTION_COUNT
    _COLLECTION_COUNT = collection.count()
    logger.info("Upsert complete. Collection now has %d items.", _COLLECTION_COUNT)


def query_collection(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = TOP_K,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Embed query_text and retrieve the top-n_results most similar chunks.
    """
    logger.info("Querying collection for: %r (top %d)", query_text, n_results)

    query_embedding = embed_texts([query_text], task_type="retrieval_query")[0]

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    raw = collection.query(**query_kwargs)

    results: list[dict[str, Any]] = []
    for i, doc_id in enumerate(raw["ids"][0]):
        results.append(
            {
                "id": doc_id,
                "document": raw["documents"][0][i],
                "metadata": raw["metadatas"][0][i],
                "distance": raw["distances"][0][i],
            }
        )

    logger.info("Query returned %d results.", len(results))
    return results