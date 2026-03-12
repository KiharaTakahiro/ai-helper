import datetime
from sqlalchemy.orm import Session
from ai_helper.db.models import Artifact


class ArtifactMetadataRepository:
    """アーティファクトメタデータテーブルへのアクセサ"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, artifact_id: str, type_: str, repository_path: str) -> Artifact:
        a = Artifact(
            id=artifact_id,
            type=type_,
            created_at=datetime.datetime.now(datetime.UTC),
            repository_path=repository_path,
        )
        self.session.add(a)
        self.session.commit()
        return a

    def get(self, artifact_id: str) -> Artifact | None:
        return self.session.get(Artifact, artifact_id)

    def list_older_than(self, cutoff: datetime.datetime) -> list[Artifact]:
        """指定日時より古いアーティファクトをリストアップする。"""
        return (
            self.session.query(Artifact)
            .filter(Artifact.created_at < cutoff)
            .all()
        )

    def delete(self, artifact_id: str) -> None:
        """指定 ID のメタデータレコードを削除する。"""
        a = self.session.get(Artifact, artifact_id)
        if a is not None:
            self.session.delete(a)
            self.session.commit()
