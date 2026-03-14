from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """
    Base interface for storage backends.
    """

    @abstractmethod
    def save(self, key: str, data: Any) -> str:
        pass

    @abstractmethod
    def load(self, key: str) -> Any:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass