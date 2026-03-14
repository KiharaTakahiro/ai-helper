from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """
    データ保存の抽象インターフェース。

    Storage は ArtifactRepository などの
    Repository 層から利用される。

    実装例:
        - MemoryStorage
        - FileStorage
        - S3Storage
        - RedisStorage

    Storage はデータ保存のみを責務とし、
    Artifact のメタデータ管理は行わない。
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

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
