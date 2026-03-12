import os
import uuid
import pickle
import time
import datetime

from ai_helper.artifact.repository import ArtifactRepository


class LocalArtifactRepository(ArtifactRepository):
    """
    ローカルファイルシステムを使ってアーティファクトを保存する実装。

    保存先ディレクトリに `artifact_id.bin` というファイルを作成し、
    pickle でシリアライズしたデータを格納する。
    オプションで ArtifactMetadataRepository を受け取り、
    保存時にメタデータテーブルへレコードを作成する。

    Attributes:
        base_dir (str): ファイル保存用ベースディレクトリ。
        metadata_repo (ArtifactMetadataRepository | None): メタデータ記録用リポジトリ。
    """

    def __init__(self, base_dir: str = "workspace", metadata_repo=None):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.metadata_repo = metadata_repo

    def _path(self, artifact_id: str):
        return os.path.join(self.base_dir, artifact_id + ".bin")

    def save(self, data, type_: str | None = None) -> str:
        """データをシリアライズしてファイルに書き込み、IDを返す。

        ``type_`` を渡すことでメタデータの型を明示できる。
        メタデータリポジトリが設定されていれば記録する。
        """

        artifact_id = str(uuid.uuid4())
        path = self._path(artifact_id)

        with open(path, "wb") as f:
            pickle.dump(data, f)

        # record metadata if repository is provided
        if self.metadata_repo is not None:
            # prefer explicit type, fall back to python type name
            type_name = type_ or type(data).__name__
            try:
                self.metadata_repo.create(
                    artifact_id=artifact_id,
                    type_=type_name,
                    repository_path=path,
                )
            except Exception:
                # metadata recording should not block main save
                pass

        return artifact_id

    def gc(self, max_age_seconds: float):
        """古いアーティファクトを削除する。メタデータリポジトリがある場合は
       そこで管理されているレコードも消去する。
        """
        if self.metadata_repo is None:
            # if no metadata, we can only remove files by timestamp
            cutoff = time.time() - max_age_seconds
            for fname in os.listdir(self.base_dir):
                path = os.path.join(self.base_dir, fname)
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.remove(path)
            return
        # use metadata to find old artifacts
        cutoff_dt = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=max_age_seconds)
        old_list = self.metadata_repo.list_older_than(cutoff_dt)
        for rec in old_list:
            path = rec.repository_path
            try:
                os.remove(path)
            except Exception:
                pass
            # remove metadata record
            try:
                self.metadata_repo.delete(rec.id)
            except Exception:
                pass

    def load(self, artifact_id):
        """IDに対応するファイルを読み込み、デシリアライズして返す"""

        path = self._path(artifact_id)

        with open(path, "rb") as f:
            return pickle.load(f)
