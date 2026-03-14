from typing import Any, Dict, List

from ai_helper.core.artifact.model import Artifact
from ai_helper.core.repository.base import Repository


class ArtifactRepository(Repository):
    """
    Artifact を管理するリポジトリ。

    Node 実行結果として生成される Artifact の
    保存・取得・削除・一覧取得を提供する。

    Repository は Artifact ドメインと Storage 実装の
    橋渡しを行う役割を持つ。

    Responsibilities
    ----------------
    - Artifact メタデータの管理
    - Storage へのデータ保存
    - Artifact の取得

    Notes
    -----
    現在はインメモリ index を使用している。
    将来的には DB 永続化へ拡張可能。
    """

    def __init__(self, storage):
        self.storage = storage
        self._index: Dict[str, Artifact] = {}

    def save(self, key: str, data: Any, metadata: Dict | None = None) -> Artifact:

        uri = self.storage.save(key, data)

        artifact = Artifact(
            id=key,
            uri=uri,
            metadata=metadata or {}
        )

        self._index[key] = artifact

        return artifact

    def load(self, key: str) -> Any:

        artifact = self._index[key]

        return self.storage.load(artifact.uri)

    def delete(self, key: str) -> None:

        artifact = self._index[key]

        self.storage.delete(artifact.uri)

        del self._index[key]

    def list(self) -> List[Artifact]:

        return list(self._index.values())