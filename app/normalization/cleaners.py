import re
import unicodedata


def clean_unicode(text: str) -> str:
    """Normalizes Unicode characters, replacing non-breaking spaces and smart punctuation."""
    if not text:
        return ""
    # Normalize to NFKC representation
    normalized = unicodedata.normalize("NFKC", text)
    # Replace non-breaking spaces and irregular whitespace
    normalized = normalized.replace("\xa0", " ").replace("\u200b", "")
    # Normalize smart quotes and dashes
    normalized = normalized.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    normalized = normalized.replace("—", "--").replace("–", "-")
    return normalized


def clean_whitespace(text: str) -> str:
    """Collapses repeated spaces/tabs and limits consecutive newlines."""
    if not text:
        return ""
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple inline spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines to double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_boilerplate(text: str) -> str:
    """Strips common noise lines, empty brackets, or separator lines."""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Drop meaningless standalone separators
        if stripped in ("---", "===", "***", "___"):
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)


def clean_text(text: str) -> str:
    """Full text cleanup pipeline: Unicode -> Whitespace -> Boilerplate."""
    return clean_boilerplate(clean_whitespace(clean_unicode(text)))
