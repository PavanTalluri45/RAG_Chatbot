import re
from typing import Dict, List, Pattern

# Extensible structure for defining conversational intents using regex patterns.
# New intents can be easily added by appending to this dictionary.
CONVERSATIONAL_INTENTS: Dict[str, List[str]] = {
    "greetings": [
        r"^hi$",
        r"^hello$",
        r"^hey$",
        r"^good\s+morning$",
        r"^good\s+afternoon$",
        r"^good\s+evening$",
    ],
    "small_talk": [
        r"^how\s+are\s+you\??$",
        r"^how's\s+it\s+going\??$",
        r"^what's\s+up\??$",
    ],
    "identity": [
        r"^who\s+are\s+you\??$",
        r"^what\s+can\s+you\s+do\??$",
    ],
    "gratitude": [
        r"^thanks$",
        r"^thank\s+you$",
        r"^appreciate\s+it$",
    ],
    "farewell": [
        r"^bye$",
        r"^goodbye$",
        r"^see\s+you$",
        r"^take\s+care$",
    ],
}


class IntentDetector:
    """
    Class responsible for checking if a user query matches conversational intents.
    Separates conversational input classification from RAG pipeline queries.
    """

    def __init__(self, intents_config: Dict[str, List[str]] = CONVERSATIONAL_INTENTS) -> None:
        self.compiled_intents: Dict[str, List[Pattern[str]]] = {}
        for intent, patterns in intents_config.items():
            self.compiled_intents[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def is_conversational(self, text: str) -> bool:
        """
        Determines whether the input text represents a conversational request.
        Normalizes input by stripping leading/trailing whitespace, punctuation,
        and trailing question marks for matching.
        """
        # Normalize: strip leading/trailing spaces and lowercase
        normalized = text.strip().lower()

        # Strip common trailing punctuation (except question mark)
        while normalized and normalized[-1] in (".", "!", ",", " "):
            normalized = normalized[:-1]

        # Strip trailing question mark for a cleaner match alternative
        cleaned_without_q = normalized
        while cleaned_without_q and cleaned_without_q[-1] in ("?",):
            cleaned_without_q = cleaned_without_q[:-1]

        for patterns in self.compiled_intents.values():
            for pattern in patterns:
                # Match against both normalized and question-mark stripped variations
                if pattern.match(normalized) or pattern.match(cleaned_without_q):
                    return True

        return False
