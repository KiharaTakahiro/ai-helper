import os
from typing import Any

from .base import Storage


class FileStorage(Storage):
    """
    ファイルシステムベースの Storage 実装。

    指定された root_dir 配下にファイルを保存する。

    Example
    -------

    root_dir = "artifacts"

    save("frame1", data)

    ↓

    artifacts/frame1
    """

    def __init__(self, root_dir: str = "artifacts"):

        self.root_dir = root_dir

        os.makedirs(self.root_dir, exist_ok=True)

    def _path(self, key: str) -> str:

        return os.path.join(self.root_dir, key)

    def save(self, key: str, data: Any) -> str:

        path = self._path(key)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        if isinstance(data, bytes):

            with open(path, "wb") as f:
                f.write(data)

        else:

            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))

        return path

    def load(self, key: str) -> Any:

        path = key

        with open(path, "rb") as f:

            return f.read()

    def delete(self, key: str) -> None:

        if os.path.exists(key):
            os.remove(key)
    
    def exists(self, key):
        return super().exists(key)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._path(key))