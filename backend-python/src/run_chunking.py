import logging
from pathlib import Path

from src.chunker import chunk_markdown, save_chunks
from src.markdown_loader import load_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / "data" / "raw" / "Employee_Handbook.md"
    output_file = base_dir / "processed" / "chunks.json"

    logger.info("Starting chunking pipeline for %s", input_file)

    markdown_text = load_markdown(str(input_file))
    chunks = chunk_markdown(markdown_text)
    save_chunks(chunks, str(output_file))

    logger.info("Chunking completed successfully")


if __name__ == "__main__":
    main()