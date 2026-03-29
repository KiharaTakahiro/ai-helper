import os
import uuid
import pickle
import time
import datetime

from ai_helper.core.repository.artifact_repository import ArtifactRepository


class LocalArtifactRepository(ArtifactRepository):
    """
    ローカルファイルシステムにアーティファクトを保存するリポジトリ。

    ------------------------------------------------------------
    ■ このクラスの役割
    ------------------------------------------------------------
    Node の実行結果（= Artifact）をファイルとして保存し、
    後から読み出せるようにする。

    内部的には以下を行う：

    1. 一意なIDを生成する（UUID）
    2. データを pickle でバイナリ化（シリアライズ）
    3. ファイルとして保存する
    4. 必要に応じてメタデータも保存する

    ------------------------------------------------------------
    ■ 保存されるファイルのイメージ
    ------------------------------------------------------------
    workspace/
        123e4567-e89b-12d3-a456-426614174000.bin
        987e6543-e21b-12d3-a456-426614174999.bin

    ------------------------------------------------------------
    ■ なぜ pickle を使うのか？
    ------------------------------------------------------------
    Pythonのオブジェクト（dict / list / クラスなど）を
    そのまま保存・復元できるため。

    ------------------------------------------------------------
    ■ Attributes
    ------------------------------------------------------------
    base_directory (str):
        アーティファクトを保存するディレクトリ

    metadata_repository:
        アーティファクトのメタ情報（型・保存先など）を管理するリポジトリ
        （無くても動作可能）
    """

    def __init__(self, base_directory: str = "workspace", metadata_repository=None):
        """
        リポジトリを初期化する。

        Args:
            base_directory (str):
                アーティファクト保存先ディレクトリ

            metadata_repository:
                メタデータ管理用リポジトリ（任意）
        """

        self.base_directory = base_directory
        self.metadata_repository = metadata_repository

        # ディレクトリが存在しない場合は作成
        os.makedirs(self.base_directory, exist_ok=True)

    def _build_file_path(self, artifact_id: str) -> str:
        """
        アーティファクトIDから実際のファイルパスを生成する。

        Args:
            artifact_id (str):
                アーティファクトID（UUID）

        Returns:
            str:
                ファイルパス（例: workspace/xxx.bin）
        """
        return os.path.join(self.base_directory, f"{artifact_id}.bin")

    def save(self, data, artifact_type: str | None = None) -> str:
        """
        データを保存し、アーティファクトIDを返す。

        ------------------------------------------------------------
        ■ 処理の流れ
        ------------------------------------------------------------
        1. UUIDを生成（アーティファクトID）
        2. 保存先パスを決定
        3. pickleでシリアライズしてファイル保存
        4. メタデータがあればDB等に記録
        5. アーティファクトIDを返す

        ------------------------------------------------------------
        ■ なぜIDを返すのか？
        ------------------------------------------------------------
        実際のデータではなく「参照」を扱うため。
        → パイプラインは軽量になる

        Args:
            data:
                保存したいデータ（任意のPythonオブジェクト）

            artifact_type (str | None):
                データの型（省略時は自動推定）

        Returns:
            str:
                生成されたアーティファクトID
        """

        # -------------------------
        # ① 一意なIDを生成
        # -------------------------
        artifact_id = str(uuid.uuid4())

        # -------------------------
        # ② 保存パスを決定
        # -------------------------
        file_path = self._build_file_path(artifact_id)

        # -------------------------
        # ③ データをファイルに保存（pickle）
        # -------------------------
        with open(file_path, "wb") as file:
            pickle.dump(data, file)

        # -------------------------
        # ④ メタデータ記録（任意）
        # -------------------------
        if self.metadata_repository is not None:
            # 型が指定されていなければ Python の型名を使う
            resolved_type = artifact_type or type(data).__name__

            try:
                self.metadata_repository.create(
                    artifact_id=artifact_id,
                    type_=resolved_type,
                    repository_path=file_path,
                )
            except Exception:
                """
                メタデータ保存は「補助機能」なので、
                失敗してもメイン処理は止めない。
                """
                pass

        return artifact_id

    def load(self, artifact_id: str):
        """
        アーティファクトIDからデータを読み込む。

        ------------------------------------------------------------
        ■ 処理の流れ
        ------------------------------------------------------------
        1. ファイルパスを生成
        2. ファイルを開く
        3. pickleでデシリアライズ

        Args:
            artifact_id (str):
                読み込み対象のID

        Returns:
            Any:
                復元されたデータ
        """

        file_path = self._build_file_path(artifact_id)

        with open(file_path, "rb") as file:
            return pickle.load(file)

    def gc(self, max_age_seconds: float):
        """
        古いアーティファクトを削除する（ガベージコレクション）。

        ------------------------------------------------------------
        ■ 2つの動作モード
        ------------------------------------------------------------

        【1】メタデータなし
            → ファイルの更新時刻で判断して削除

        【2】メタデータあり
            → DBの情報を元に削除（より正確）

        Args:
            max_age_seconds (float):
                この秒数より古いものを削除する
        """

        # -------------------------
        # メタデータがない場合
        # -------------------------
        if self.metadata_repository is None:
            cutoff_timestamp = time.time() - max_age_seconds

            for file_name in os.listdir(self.base_directory):
                file_path = os.path.join(self.base_directory, file_name)

                if not os.path.isfile(file_path):
                    continue

                file_modified_time = os.path.getmtime(file_path)

                if file_modified_time < cutoff_timestamp:
                    os.remove(file_path)

            return

        # -------------------------
        # メタデータがある場合
        # -------------------------
        cutoff_datetime = (
            datetime.datetime.now(datetime.UTC)
            - datetime.timedelta(seconds=max_age_seconds)
        )

        old_records = self.metadata_repository.list_older_than(cutoff_datetime)

        for record in old_records:
            file_path = record.repository_path

            # ファイル削除
            try:
                os.remove(file_path)
            except Exception:
                pass

            # メタデータ削除
            try:
                self.metadata_repository.delete(record.id)
            except Exception:
                pass