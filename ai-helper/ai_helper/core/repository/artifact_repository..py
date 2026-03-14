from typing import Any, Dict, List

from ai_helper.core.artifact.model import Artifact
from ai_helper.core.repository.base import Repository


class ArtifactRepository(Repository):
    """
    Repository responsible for managing artifacts.
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