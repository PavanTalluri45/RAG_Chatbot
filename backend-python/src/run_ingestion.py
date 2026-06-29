import json
import logging
from pathlib import Path
from src.vector_store import get_chroma_client, get_or_create_collection, upsert_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    chunks_file = base_dir / "processed" / "chunks.json"

    if not chunks_file.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {chunks_file}\n"
            "Run run_chunking.py first to generate it."
        )

    logger.info("Loading chunks from %s …", chunks_file)
    with open(chunks_file, encoding="utf-8") as fh:
        chunks = json.load(fh)
    logger.info("Loaded %d chunks.", len(chunks))

    client = get_chroma_client()
    collection = get_or_create_collection(client)
    upsert_chunks(collection, chunks)

    logger.info("Ingestion finished successfully.")


if __name__ == "__main__":
    main()