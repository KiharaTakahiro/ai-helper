import os
from typing import Any

from .base import Storage


class FileStorage(Storage):
    """
    ローカルファイルシステムを使用した Storage 実装クラス。

    -----------------------------
    ■ このクラスの役割
    -----------------------------
    ArtifactRepository から渡されたデータを、
    「実際にファイルとして保存・取得・削除」する責務を持つ。

    Repository が「論理管理」なのに対して、
    Storage は「物理保存」を担当する。

    -----------------------------
    ■ 保存イメージ
    -----------------------------
    root_dir = "artifacts"

    save("image/frame1.png", data)

    ↓ 実際に保存されるパス

    artifacts/image/frame1.png

    -----------------------------
    ■ key と path の違い（重要）
    -----------------------------
    key:
        Repository から渡される「論理キー」
        例: "image/frame1.png"

    path:
        実際のファイルパス
        例: "artifacts/image/frame1.png"

    -----------------------------
    ■ 注意点
    -----------------------------
    - key はそのままファイル名として使われる
    - ディレクトリ構造も key に含めることができる
    """

    def __init__(self, root_directory: str = "artifacts"):
        """
        FileStorage を初期化する。

        -----------------------------
        ■ Args
        -----------------------------
        root_directory (str):
            ファイルを保存するルートディレクトリ

        -----------------------------
        ■ 処理内容
        -----------------------------
        - ルートディレクトリを作成（存在しなければ）
        """

        self.root_directory = root_directory

        # 保存先ディレクトリを作成（既に存在する場合は何もしない）
        os.makedirs(self.root_directory, exist_ok=True)

    def _build_file_path(self, artifact_key: str) -> str:
        """
        Artifact のキーから実際のファイルパスを生成する。

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            Artifact の識別キー

        -----------------------------
        ■ Returns
        -----------------------------
        str:
            実際のファイルパス
        """

        return os.path.join(self.root_directory, artifact_key)

    def save(self, artifact_key: str, data: Any) -> str:
        """
        データをファイルとして保存する。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. ファイルパスを生成
        2. 必要なディレクトリを作成
        3. データ型に応じて書き込み方法を分岐
        4. 保存したパスを返す

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            保存する Artifact のキー

        data (Any):
            保存するデータ

        -----------------------------
        ■ Returns
        -----------------------------
        str:
            保存されたファイルのパス（URIとして扱う）
        """

        # -------------------------
        # ① 保存先パス生成
        # -------------------------
        file_path = self._build_file_path(artifact_key)

        # -------------------------
        # ② ディレクトリ作成
        # -------------------------
        # 例: artifacts/image/frame1.png の場合
        # artifacts/image を作る
        directory_path = os.path.dirname(file_path)
        os.makedirs(directory_path, exist_ok=True)

        # -------------------------
        # ③ データ保存
        # -------------------------
        if isinstance(data, bytes):
            # バイナリデータとして保存（画像・音声など）
            with open(file_path, "wb") as file:
                file.write(data)
        else:
            # テキストデータとして保存
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(str(data))

        return file_path

    def load(self, file_path: str) -> Any:
        """
        ファイルを読み込み、データを返す。

        -----------------------------
        ■ 注意（重要）
        -----------------------------
        ここで受け取るのは「keyではなく path（URI）」である。

        なぜなら Repository がすでに path を管理しているため。

        -----------------------------
        ■ Args
        -----------------------------
        file_path (str):
            読み込むファイルのパス

        -----------------------------
        ■ Returns
        -----------------------------
        Any:
            読み込まれたデータ（bytes）
        """

        with open(file_path, "rb") as file:
            return file.read()

    def delete(self, file_path: str) -> None:
        """
        ファイルを削除する。

        -----------------------------
        ■ Args
        -----------------------------
        file_path (str):
            削除対象のファイルパス
        """

        if os.path.exists(file_path):
            os.remove(file_path)

    def exists(self, artifact_key: str) -> bool:
        """
        指定したキーのファイルが存在するかを確認する。

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            確認対象のキー

        -----------------------------
        ■ Returns
        -----------------------------
        bool:
            存在する場合 True
        """

        file_path = self._build_file_path(artifact_key)
        return os.path.exists(file_path)