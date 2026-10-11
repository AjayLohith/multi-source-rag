"""
Every source (PDF, CSV, SQL — and Web/API on Day 3) implements this
interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.contracts import RawDocument, SourceDescriptor


class SourceAdapter(ABC):
    def __init__(self, descriptor: SourceDescriptor):
        self.descriptor = descriptor

    def validate(self) -> None:
        """Raise ValueError if descriptor.config is missing something this
        adapter needs. Default: nothing required. Each concrete adapter
        overrides this with its own required config keys."""
        return None

    @abstractmethod
    def fetch(self) -> AsyncIterator[RawDocument]:
        """Yield RawDocument objects one at a time. Concrete subclasses
        implement this as `async def fetch(self):` with `yield` statements
        (an async generator) — declared here as a plain abstract method
        since it's never called directly on the base class."""
        raise NotImplementedError
