"""
Typed exceptions for extraction errors across all source types.
Carries source_ref and error_code so that downstream Dead-Letter Queues (DLQ)
and monitoring can capture and triage failures deterministically.
"""


class ExtractionError(Exception):
    """Base class for all extraction errors."""

    def __init__(self, message: str, source_ref: str, error_code: str):
        super().__init__(message)
        self.message = message
        self.source_ref = source_ref
        self.error_code = error_code

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message} (source: {self.source_ref})"


class PDFExtractionError(ExtractionError):
    pass


class CSVExtractionError(ExtractionError):
    pass


class SQLExtractionError(ExtractionError):
    pass


class OCRError(ExtractionError):
    pass


class WebExtractionError(ExtractionError):
    pass


class APIExtractionError(ExtractionError):
    pass


class DocExtractionError(ExtractionError):
    pass


class TextExtractionError(ExtractionError):
    pass


class JSONExtractionError(ExtractionError):
    pass
