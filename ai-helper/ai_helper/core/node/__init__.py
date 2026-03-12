"""Core node subpackage containing base Node class."""

from abc import ABC, abstractmethod
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class Node(ABC):
    """
    パイプライン内の各処理（ノード）の基底クラス。

    サブクラスは `inputs`/`outputs` で要求するアーティファクト論理名を定義し、
    `run` メソッドで実際の処理を行う。コンテキストとアーティファクト
    リポジトリが渡される。

    Attributes:
        inputs (list[str]): 必要とする入力アーティファクト名のリスト。
        outputs (list[str]): 出力するアーティファクト名のリスト。
    """

    inputs: list[str] = []
    outputs: list[str] = []

    @abstractmethod
    def run(self, context: Context, artifact_repo:ArtifactRepository):
        """ノード処理を実行するエントリポイント。

        Args:
            context (Context): 現在のパイプライン実行コンテキスト。
            artifact_repo (ArtifactRepository): アーティファクト保存/読み込み用リポジトリ。
        """
        pass
