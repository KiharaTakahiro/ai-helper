from abc import ABC, abstractmethod
from typing import Any, List


class Repository(ABC):
    """
    Repository の基底インターフェース。

    データ保存層の抽象化を目的とする。

    主な操作
    - save
    - load
    - delete
    - list
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