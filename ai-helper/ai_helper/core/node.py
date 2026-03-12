from abc import ABC, abstractmethod
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository

# BaseNode は新しいプラグイン仕様で使われる抽象基底クラス
from ai_helper.core.node.base_node import BaseNode


class Node(BaseNode):
    """
    パイプライン内の各処理（ノード）の基底クラス。

    旧来の ``run`` インターフェースを保持しつつ、
    ``BaseNode`` の抽象メソッド ``execute`` を実装する。

    ``inputs``/``outputs`` によるアーティファクト仕様は従来通り。

    Attributes:
        inputs (list[str]): 必要とする入力アーティファクト名のリスト。
        outputs (list[str]): 出力するアーティファクト名のリスト。
    """

    inputs: list[str] = []
    outputs: list[str] = []

    def run(self, context: Context, artifact_repo:ArtifactRepository):
        """ノード処理を実行するエントリポイント。

        Args:
            context (Context): 現在のパイプライン実行コンテキスト。
            artifact_repo (ArtifactRepository): アーティファクト保存/読み込み用リポジトリ。
        """
        pass

    # BaseNode 用のラッパーメソッド
    def execute(self, context, runtime):
        """BaseNode 抽象メソッドの実装。

        既存コードでは ``runtime`` として ``ArtifactRepository`` を渡すため、
        そのまま ``run`` を呼び出す。
        """
        # runtime は旧来の artifact_repo に相当
        return self.run(context, runtime)
