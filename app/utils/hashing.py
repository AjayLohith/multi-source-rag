import hashlib


def sha256_text(text: str) -> str:
    """Computes a deterministic SHA-256 hash string for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
