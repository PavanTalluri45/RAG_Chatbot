import json
import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

HEADERS_TO_SPLIT_ON: list[tuple[str, str]] = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 150
MIN_CHUNK_CHARS: int = 200

# Sentinel used to protect tables from being split.
# Must not appear in normal markdown.
_TABLE_SENTINEL_OPEN = "\n\x02TABLE_START\x03\n"
_TABLE_SENTINEL_CLOSE = "\n\x02TABLE_END\x03\n"
_SENTINEL_RE = re.compile(
    r"\x02TABLE_START\x03(.*?)\x02TABLE_END\x03",
    re.DOTALL,
)

# A markdown table line begins with an optional pipe or cell content followed
# by a pipe.  The separator row (|---|---) is also captured.
_TABLE_LINE_RE = re.compile(r"^\s*\|")


# ---------------------------------------------------------------------------
# Stage 3: Table Protection
# ---------------------------------------------------------------------------

def _is_table_line(line: str) -> bool:
    """Return True when *line* looks like a markdown table row."""
    return bool(_TABLE_LINE_RE.match(line))


def _protect_tables(text: str) -> str:
    """
    Wrap every contiguous block of markdown table lines with sentinels so
    that RecursiveCharacterTextSplitter treats each table as a single atom.

    Parameters
    ----------
    text:
        Document page_content string (post Stage-2 split).

    Returns
    -------
    str
        Text with table blocks wrapped in sentinel delimiters.
    """
    lines = text.split("\n")
    result: list[str] = []
    in_table = False

    for line in lines:
        if _is_table_line(line):
            if not in_table:
                result.append(_TABLE_SENTINEL_OPEN.strip())
                in_table = True
            result.append(line)
        else:
            if in_table:
                result.append(_TABLE_SENTINEL_CLOSE.strip())
                in_table = False
            result.append(line)

    if in_table:
        result.append(_TABLE_SENTINEL_CLOSE.strip())

    return "\n".join(result)


def _restore_sentinels(text: str) -> str:
    """
    Remove sentinels from *text*, returning clean content.
    The table rows themselves are preserved exactly as-is.
    """
    text = text.replace("\x02TABLE_START\x03", "")
    text = text.replace("\x02TABLE_END\x03", "")
    return text.strip()


def _split_preserving_tables(
    text: str,
    char_splitter: RecursiveCharacterTextSplitter,
) -> list[str]:
    """
    Split *text* with *char_splitter* while keeping table blocks atomic.

    Algorithm
    ---------
    1. Tokenise the text into alternating non-table / table segments.
    2. For each segment:
       - Table segment  → emit as a single chunk (never split).
       - Text segment   → delegate to ``char_splitter.split_text``.
    3. Concatenate all resulting pieces.

    Parameters
    ----------
    text:
        Page content with table sentinels already injected.
    char_splitter:
        Configured RecursiveCharacterTextSplitter instance.

    Returns
    -------
    list[str]
        Ordered list of content strings, each ≤ CHUNK_SIZE (tables may
        exceed this limit intentionally rather than being split).
    """
    # Split on sentinel boundaries; even indices = plain text, odd = tables
    parts = _SENTINEL_RE.split(text)
    pieces: list[str] = []

    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue

        if i % 2 == 1:
            # Table block – emit intact
            pieces.append(part)
        else:
            # Plain text – apply character splitter
            sub_chunks = char_splitter.split_text(part)
            pieces.extend(c.strip() for c in sub_chunks if c.strip())

    return pieces


# ---------------------------------------------------------------------------
# Stage 5: Tiny Chunk Merger
# ---------------------------------------------------------------------------

def _same_context(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Return True when chunks *a* and *b* share the same section+heading."""
    return a["section"] == b["section"] and a["heading"] == b["heading"]


def _merge_tiny_chunks(
    chunks: list[dict[str, Any]],
    min_chars: int = MIN_CHUNK_CHARS,
    max_chars: int = CHUNK_SIZE * 2,
) -> list[dict[str, Any]]:
    """
    Merge chunks whose content is shorter than *min_chars* into an adjacent
    chunk with the same section/heading context.

    Merge priority
    --------------
    1. Prefer merging with the **previous** chunk (same context).
    2. Otherwise merge forward with the **next** chunk.
    3. If neither neighbour shares context, keep the tiny chunk as-is
       (avoids cross-section contamination).

    The merged content never exceeds *max_chars* to avoid super-chunks.

    Parameters
    ----------
    chunks:
        Raw list of chunk dicts produced by Stage 4.
    min_chars:
        Chunks shorter than this threshold are candidates for merging.
    max_chars:
        Upper bound on merged chunk size.

    Returns
    -------
    list[dict[str, Any]]
        Deduplicated, renumbered list of chunks.
    """
    if not chunks:
        return chunks

    merged: list[dict[str, Any]] = list(chunks)  # work on a copy
    changed = True

    while changed:
        changed = False
        new_merged: list[dict[str, Any]] = []
        skip_next = False

        for i, chunk in enumerate(merged):
            if skip_next:
                skip_next = False
                continue

            content = chunk["content"]

            if len(content) < min_chars:
                prev_ok = (
                    i > 0
                    and _same_context(new_merged[-1], chunk)
                    and len(new_merged[-1]["content"]) + len(content) <= max_chars
                ) if new_merged else False

                next_ok = (
                    i < len(merged) - 1
                    and _same_context(chunk, merged[i + 1])
                    and len(content) + len(merged[i + 1]["content"]) <= max_chars
                )

                if prev_ok:
                    # Merge into previous
                    new_merged[-1]["content"] = (
                        new_merged[-1]["content"].rstrip()
                        + "\n\n"
                        + content.lstrip()
                    )
                    logger.debug(
                        "Merged tiny chunk (backward): '%s…'",
                        content[:60],
                    )
                    changed = True
                    continue

                elif next_ok:
                    # Merge forward
                    next_chunk = merged[i + 1]
                    chunk["content"] = (
                        content.rstrip()
                        + "\n\n"
                        + next_chunk["content"].lstrip()
                    )
                    new_merged.append(chunk)
                    skip_next = True
                    logger.debug(
                        "Merged tiny chunk (forward): '%s…'",
                        content[:60],
                    )
                    changed = True
                    continue

            new_merged.append(chunk)

        merged = new_merged

    # Re-number chunk IDs
    for idx, chunk in enumerate(merged, start=1):
        chunk["chunk_id"] = idx

    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_markdown(
    markdown_text: str,
    source_file: str = "Employee_Handbook.md",
) -> list[dict[str, Any]]:
    """
    Run the full 4-stage chunking pipeline (Stages 2-5) and return a list of
    chunk dictionaries ready for serialisation.

    Pipeline
    --------
    Stage 2  –  MarkdownHeaderTextSplitter
    Stage 3  –  Table protection (sentinel injection)
    Stage 4  –  RecursiveCharacterTextSplitter (table-aware)
    Stage 5  –  Tiny chunk merger

    Parameters
    ----------
    markdown_text:
        Cleaned markdown string returned by ``load_markdown``.
    source_file:
        Value to embed in every chunk's ``source_file`` field.

    Returns
    -------
    list[dict[str, Any]]
        Ordered list of chunk dicts with keys:
        chunk_id, section, heading, subheading, source_file, content.
    """
    # ── Stage 2: split by markdown headers ───────────────────────────────
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    md_docs: list[Document] = md_splitter.split_text(markdown_text)
    logger.info("Stage 2 complete: %d header-based documents", len(md_docs))

    # ── Stage 3 + 4: table protection + character splitting ───────────────
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    raw_chunks: list[dict[str, Any]] = []
    chunk_counter = 0

    for doc in md_docs:
        protected_text = _protect_tables(doc.page_content)
        pieces = _split_preserving_tables(protected_text, char_splitter)

        for piece in pieces:
            clean_piece = _restore_sentinels(piece)
            if not clean_piece:
                continue
            chunk_counter += 1
            raw_chunks.append(
                {
                    "chunk_id": chunk_counter,
                    "section": doc.metadata.get("h1", ""),
                    "heading": doc.metadata.get("h2", ""),
                    "subheading": doc.metadata.get("h3", ""),
                    "source_file": source_file,
                    "content": clean_piece,
                }
            )

    logger.info(
        "Stage 3+4 complete: %d chunks after table-safe character split",
        len(raw_chunks),
    )

    # ── Stage 5: merge tiny chunks ────────────────────────────────────────
    final_chunks = _merge_tiny_chunks(raw_chunks)
    logger.info(
        "Stage 5 complete: %d chunks after tiny-chunk merge  "
        "(%d removed)",
        len(final_chunks),
        len(raw_chunks) - len(final_chunks),
    )

    return final_chunks


def save_chunks(
    chunks: list[dict[str, Any]],
    output_file: str,
) -> None:
    """
    Serialise *chunks* to a pretty-printed JSON file at *output_file*.

    Parameters
    ----------
    chunks:
        List of chunk dicts produced by ``chunk_markdown``.
    output_file:
        Destination file path (parent directories are created automatically).
    """
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(chunks, fh, indent=2, ensure_ascii=False)

    logger.info("Saved %d chunks → %s", len(chunks), output_file)
