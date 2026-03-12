"""Core context subpackage."""

from typing import Dict


class Context:
    """
    パイプライン実行時の共有コンテキスト。

    ノード間でアーティファクトIDを受け渡すための辞書を保持する。
    名前とIDのペアを保存し、必要に応じて取得できる。

    Attributes:
        artifacts (Dict[str, str]): アーティファクト名 -> アーティファクトID
    """

    def __init__(self):
        self.artifacts: Dict[str, str] = {}

    def set_artifact(self, name: str, artifact_id: str):
        """名前付きアーティファクトIDをコンテキストに保存する。

        Args:
            name (str): 識別用の論理名。
            artifact_id (str): アーティファクトリポジトリ内のID。
        """
        # 既存のキーを上書きする場合もあるため単純代入でよい
        self.artifacts[name] = artifact_id

    def get_artifact(self, name: str) -> str:
        """指定した論理名に対応するアーティファクトIDを返す。

        Args:
            name (str): 取得したいアーティファクトの論理名。

        Returns:
            str: 保存されているアーティファクトID。

        Raises:
            KeyError: 指定した名前が存在しない場合。
        """
        return self.artifacts[name]
