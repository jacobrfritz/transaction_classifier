import re
from typing import Optional

from sentence_transformers import SentenceTransformer

# Lazy loader for the model
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def clean_text(raw_string: str) -> str:
    """
    Lowercases, removes dates, strips digits, and removes junk prefixes.
    """
    if not raw_string:
        return ""

    # Lowercase
    text = raw_string.lower()

    # Remove dates (simple YYYY-MM-DD or MM/DD/YYYY or DD-MM-YYYY)
    text = re.sub(r"\d{2,4}[-/]\d{1,2}[-/]\d{1,4}", "", text)

    # Remove junk prefixes (TST*, etc.)
    text = re.sub(r"^[a-z]{2,4}\*", "", text)

    # Remove digits
    text = re.sub(r"\d+", "", text)

    # Remove special characters and extra whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_embedding(text: str) -> list[float]:
    """
    Returns a 384-float list representing the embedding of the text.
    """
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()
