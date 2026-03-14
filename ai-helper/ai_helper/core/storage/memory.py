from typing import Any
from .base import Storage


class MemoryStorage(Storage):
    """
    メモリ上にデータを保存するストレージ実装。

    主に以下用途で使用する

    - テスト
    - 一時的なパイプライン実行
    - 開発時の簡易ストレージ
    """

    def __init__(self):
        self._store: dict[str, Any] = {}

    def save(self, key: str, data: Any) -> str:

        self._store[key] = data

        return key

    def load(self, key: str) -> Any:

        return self._store[key]

    def delete(self, key: str) -> None:

        del self._store[key]
    
    def exists(self, key: str) -> bool:
        return key in self._store