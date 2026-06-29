import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Noise patterns – lines that match any of these are dropped completely.
# ---------------------------------------------------------------------------
_NOISE_PATTERNS: list[str] = [
    r"^NovaSprint Labs, Inc\.\s*$",
    r"^Page \d+ of \d+\s*$",
    r"^novasprintlabs\.com\s*$",
    r"^NovaSprint Labs — Employee Handbook\s*$",
    r"^Internal Use Only\s*$",
]

# ---------------------------------------------------------------------------
# TOC heading detection – H2 headings that signal the start of the TOC block.
# The entire block between the first TOC marker and the first real SECTION
# header is discarded.
# ---------------------------------------------------------------------------
_TOC_HEADING_PATTERN = re.compile(
    r"^##\s*\*\*(?:TABLE OF CONTENTS|What's Inside This Handbook"
    r"|Getting to Know Us)\*\*\s*$",
    re.IGNORECASE,
)

# Detects the first real content section (# SECTION X ...) written in bold.
_SECTION_HEADER_PATTERN = re.compile(
    r"^##\s*\*\*(SECTION \d+.*?)\*\*\s*$"
)

# Detects a plain bold heading that is NOT a section header.
_BOLD_HEADING_PATTERN = re.compile(r"^##\s*\*\*(.*?)\*\*\s*$")


def _remove_toc(lines: list[str]) -> list[str]:
    """
    Locate and strip the Table of Contents block.

    Strategy
    --------
    Walk the lines until we hit the first TOC heading.  From that point,
    continue skipping lines until we encounter the first ``## **SECTION …**``
    header, which marks the beginning of actual document content.  Everything
    between those two points (inclusive of the TOC heading) is discarded.
    """
    in_toc = False
    result: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not in_toc:
            # Detect entry into TOC
            if _TOC_HEADING_PATTERN.match(stripped):
                in_toc = True
                logger.debug("TOC block started at: %s", stripped)
                continue
            result.append(line)
        else:
            # Stay in TOC until we see the first real section header
            if _SECTION_HEADER_PATTERN.match(stripped):
                in_toc = False
                logger.debug("TOC block ended; resuming at: %s", stripped)
                result.append(line)  # keep the section header itself
            # else: discard the TOC line

    return result


def clean_markdown(text: str) -> str:
    """
    Full sanitation pass on raw markdown text.

    Steps
    -----
    1. Split into lines.
    2. Drop noise lines (footers, page numbers, etc.).
    3. Remove the TOC block.
    4. Normalise ``## **SECTION X …**``  →  ``# SECTION X …``  (H1).
    5. Deduplicate section headers (keep only first occurrence).
    6. Normalise ``## **Heading**``  →  ``## Heading``  (H2).
    7. Collapse excessive blank lines.

    Parameters
    ----------
    text:
        Raw markdown string read from disk.

    Returns
    -------
    str
        Sanitised markdown ready for the splitter pipeline.
    """
    lines = text.split("\n")

    # ── Step 1: drop noise lines ──────────────────────────────────────────
    filtered: list[str] = []
    for line in lines:
        stripped = line.strip()
        is_noise = any(re.match(p, stripped) for p in _NOISE_PATTERNS)
        if not is_noise:
            filtered.append(line)

    # ── Step 2: remove TOC block ──────────────────────────────────────────
    filtered = _remove_toc(filtered)

    # ── Steps 3-6: normalise headers + deduplicate sections ───────────────
    seen_sections: set[str] = set()
    cleaned: list[str] = []

    for line in filtered:
        stripped = line.strip()

        # SECTION headers → H1
        sec_match = _SECTION_HEADER_PATTERN.match(stripped)
        if sec_match:
            title = sec_match.group(1).strip()
            if title in seen_sections:
                continue          # drop duplicate
            seen_sections.add(title)
            cleaned.append(f"# {title}")
            continue

        # Remaining ## **Bold** → H2 (plain bold, non-section)
        h2_match = _BOLD_HEADING_PATTERN.match(stripped)
        if h2_match:
            cleaned.append(f"## {h2_match.group(1).strip()}")
            continue

        cleaned.append(line)

    # ── Step 7: collapse excessive blank lines ────────────────────────────
    result = "\n".join(cleaned)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def load_markdown(file_path: str) -> str:
    """
    Load a markdown file from *file_path*, apply full sanitation, and return
    the cleaned text.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the ``.md`` file.

    Returns
    -------
    str
        Cleaned markdown string.

    Raises
    ------
    FileNotFoundError
        When the file does not exist at the given path.
    """
    try:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        raw_content = path.read_text(encoding="utf-8")

        clean_content = clean_markdown(raw_content)

        original_lines = len(raw_content.splitlines())
        cleaned_lines = len(clean_content.splitlines())
        logger.info(
            "Loaded '%s'  |  %d → %d lines after cleaning",
            path.name,
            original_lines,
            cleaned_lines,
        )

        return clean_content

    except Exception as exc:
        logger.error("Failed to load markdown '%s': %s", file_path, exc)
        raise