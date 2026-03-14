"""Core node subpackage containing base Node class."""

from abc import ABC, abstractmethod
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository

# プラグイン対応用に BaseNode から継承
from ai_helper.core.node.base_node import BaseNode


class Node(BaseNode):
    """パイプライン内の各処理（ノード）の基底クラス。

    旧来の ``run`` インターフェースを保持しつつ、
    ``BaseNode`` の抽象メソッド ``execute`` を実装する。
    ``inputs``/``outputs`` によるアーティファクト仕様は従来通り。
    """

    inputs: list[str] = []
    outputs: list[str] = []

    @abstractmethod
    def run(self, context: Context, artifact_repo:ArtifactRepository):
        """ノード処理を実行するエントリポイント。

        Args:
            context (Context): パイプライン実行コンテキスト。
            artifact_repo (ArtifactRepository): アーティファクト保存/読み込み用リポジトリ。
        """
        pass

    # BaseNode インターフェースを満たすためのブリッジ
    def execute(self, context, runtime):
        return self.run(context, runtime)
