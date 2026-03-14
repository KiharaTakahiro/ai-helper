from typing import Any
from .base import Storage


class MemoryStorage(Storage):
    """
    In-memory storage backend.
    Useful for testing or temporary pipelines.
    """

    def __init__(self):
        self._store = {}

    def save(self, key: str, data: Any) -> str:

        self._store[key] = data

        return key

    def load(self, key: str) -> Any:

        return self._store[key]

    def delete(self, key: str) -> None:

        del self._store[key]
    
    def exists(self, key: str) -> bool:
        return key in self._store