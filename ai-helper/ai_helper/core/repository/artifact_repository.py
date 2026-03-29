from typing import Any, Dict, List, Optional

from ai_helper.core.artifact.model import Artifact
from ai_helper.core.repository.base import Repository


class ArtifactRepository(Repository):
    """
    Artifact（データ本体 + メタ情報）を管理するリポジトリクラス。

    -----------------------------
    ■ Artifact とは？
    -----------------------------
    Artifact は Node の実行結果として生成される「データの単位」であり、
    以下の情報を持つ：

        - id        : 一意な識別子（キー）
        - uri       : 実際の保存場所（Storage 側のパス）
        - metadata  : 型情報や補足情報

    -----------------------------
    ■ このクラスの役割
    -----------------------------
    Repository は「ドメイン」と「ストレージ」の橋渡しをする。

    このクラスは：

        「Artifactという概念」と
        「実際の保存処理（Storage）」を分離する

    つまり：

        Node → Repository → Storage

    という責務分離を実現する。

    -----------------------------
    ■ Responsibilities
    -----------------------------
    1. Artifact のメタ情報管理（id / uri / metadata）
    2. Storage へのデータ保存・取得・削除の委譲
    3. Artifact の一覧管理（インメモリ）

    -----------------------------
    ■ Notes
    -----------------------------
    - 現在はインメモリで Artifact を管理している
    - 将来的に DB や外部ストレージへ拡張可能
    - Storage 実装を差し替えることで S3 / ローカル / DB など対応可能
    """

    def __init__(self, storage):
        """
        ArtifactRepository を初期化する。

        -----------------------------
        ■ Args
        -----------------------------
        storage:
            実際のデータ保存・取得を行うストレージ実装

            例:
                - ローカルファイルストレージ
                - S3
                - DB
        """

        # 実データの保存・取得を担当するストレージ
        self.storage = storage

        # Artifact のメタ情報を保持するインデックス
        # key (artifact_id) → Artifact オブジェクト
        self._artifact_index: Dict[str, Artifact] = {}

    def save(
        self,
        artifact_id: str,
        data: Any,
        metadata: Optional[Dict] = None
    ) -> Artifact:
        """
        データを保存し、Artifact を生成・登録する。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. storage にデータ本体を保存
        2. 保存先 URI を取得
        3. Artifact オブジェクトを生成
        4. インデックスに登録
        5. Artifact を返却

        -----------------------------
        ■ Args
        -----------------------------
        artifact_id (str):
            Artifact の一意識別子

        data (Any):
            保存したいデータ本体

        metadata (Dict | None):
            型情報などの補助情報

        -----------------------------
        ■ Returns
        -----------------------------
        Artifact:
            保存された Artifact オブジェクト
        """

        # -------------------------
        # ① データをストレージへ保存
        # -------------------------
        # storage は実際の保存処理を担当する（ファイル・S3など）
        storage_uri = self.storage.save(artifact_id, data)

        # -------------------------
        # ② Artifact オブジェクト生成
        # -------------------------
        artifact = Artifact(
            id=artifact_id,
            uri=storage_uri,
            metadata=metadata or {}
        )

        # -------------------------
        # ③ インデックスに登録
        # -------------------------
        # これにより高速に参照できる（DBの代替）
        self._artifact_index[artifact_id] = artifact

        return artifact

    def load(self, artifact_id: str) -> Any:
        """
        Artifact を取得し、データ本体をロードする。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. インデックスから Artifact を取得
        2. Artifact の URI を使って storage からデータ取得

        -----------------------------
        ■ Args
        -----------------------------
        artifact_id (str):
            取得したい Artifact の ID

        -----------------------------
        ■ Returns
        -----------------------------
        Any:
            保存されていたデータ本体

        -----------------------------
        ■ Raises
        -----------------------------
        KeyError:
            指定した Artifact が存在しない場合
        """

        # -------------------------
        # ① Artifact メタ情報取得
        # -------------------------
        artifact = self._artifact_index[artifact_id]

        # -------------------------
        # ② 実データ取得
        # -------------------------
        return self.storage.load(artifact.uri)

    def delete(self, artifact_id: str) -> None:
        """
        Artifact を削除する（メタ情報 + 実データ）。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. インデックスから Artifact を取得
        2. storage からデータ削除
        3. インデックスから削除

        -----------------------------
        ■ Args
        -----------------------------
        artifact_id (str):
            削除対象の Artifact ID
        """

        # -------------------------
        # ① Artifact 取得
        # -------------------------
        artifact = self._artifact_index[artifact_id]

        # -------------------------
        # ② 実データ削除
        # -------------------------
        self.storage.delete(artifact.uri)

        # -------------------------
        # ③ インデックス削除
        # -------------------------
        del self._artifact_index[artifact_id]

    def list(self) -> List[Artifact]:
        """
        現在登録されているすべての Artifact を取得する。

        -----------------------------
        ■ Returns
        -----------------------------
        List[Artifact]:
            Artifact の一覧

        -----------------------------
        ■ 用途
        -----------------------------
        - デバッグ
        - 状態確認
        - 可視化
        """

        return list(self._artifact_index.values())