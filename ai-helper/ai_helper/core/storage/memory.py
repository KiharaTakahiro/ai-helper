from typing import Any, Dict

from .base import Storage


class MemoryStorage(Storage):
    """
    メモリ上にデータを保存する Storage 実装クラス。

    -----------------------------
    ■ このクラスの役割
    -----------------------------
    データを「ファイルやDBではなく、Pythonのメモリ上」に保存する。

    FileStorage がディスク保存なのに対し、
    MemoryStorage は一時的な保存を目的とする。

    -----------------------------
    ■ 主な用途
    -----------------------------
    - テスト（ファイルを使わず高速に実行）
    - 一時的なパイプライン実行
    - 開発中の簡易検証

    -----------------------------
    ■ 特徴
    -----------------------------
    - 超高速（I/Oなし）
    - プロセス終了でデータは消える
    - 永続化されない

    -----------------------------
    ■ key と URI の扱い（重要）
    -----------------------------
    FileStorage:
        key → path に変換される

    MemoryStorage:
        key = そのまま保存キー（＝URIとして扱う）

    つまりこのクラスでは：

        "key と URI は同じもの"

    になる
    """

    def __init__(self):
        """
        MemoryStorage を初期化する。

        -----------------------------
        ■ 内部構造
        -----------------------------
        _memory_store:
            key → data の辞書

        例:
            {
                "image1": b"...",
                "text1": "hello"
            }
        """

        # メモリ上のデータ保存領域
        self._memory_store: Dict[str, Any] = {}

    def save(self, artifact_key: str, data: Any) -> str:
        """
        データをメモリ上に保存する。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. key を使ってデータを辞書に格納
        2. key をそのまま返す（URIとして扱う）

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            データの識別キー

        data (Any):
            保存するデータ

        -----------------------------
        ■ Returns
        -----------------------------
        str:
            保存されたデータの識別子（URI扱い）
        """

        # -------------------------
        # ① メモリに保存
        # -------------------------
        self._memory_store[artifact_key] = data

        # -------------------------
        # ② key をそのまま返す
        # -------------------------
        # FileStorage では path を返すが、
        # MemoryStorage では key 自体がURIになる
        return artifact_key

    def load(self, artifact_key: str) -> Any:
        """
        メモリからデータを取得する。

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            取得したいデータのキー

        -----------------------------
        ■ Returns
        -----------------------------
        Any:
            保存されていたデータ

        -----------------------------
        ■ Raises
        -----------------------------
        KeyError:
            指定されたキーが存在しない場合
        """

        return self._memory_store[artifact_key]

    def delete(self, artifact_key: str) -> None:
        """
        メモリ上のデータを削除する。

        -----------------------------
        ■ Args
        -----------------------------
        artifact_key (str):
            削除対象のキー
        """

        del self._memory_store[artifact_key]

    def exists(self, artifact_key: str) -> bool:
        """
        指定したキーのデータが存在するかを確認する。

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

        return artifact_key in self._memory_store