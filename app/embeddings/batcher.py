from typing import Iterator, List, TypeVar

T = TypeVar("T")


def batch_items(items: List[T], batch_size: int = 32) -> Iterator[List[T]]:
    """Yields batches of items of length batch_size."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
