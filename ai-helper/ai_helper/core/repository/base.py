from abc import ABC, abstractmethod
from typing import Any, List


class Repository(ABC):
    """
    Base repository interface.

    Provides basic CRUD-like operations.
    """

    @abstractmethod
    def save(self, key: str, data: Any):
        pass

    @abstractmethod
    def load(self, key: str) -> Any:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def list(self) -> List[Any]:
        pass