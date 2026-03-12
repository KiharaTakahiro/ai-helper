from abc import ABC, abstractmethod


class ArtifactRepository(ABC):
    """
    アーティファクトの永続化を抽象化したインターフェース。

    実装クラスは `save`/`load` を提供し、
    データをストアに書き込んだり読み出したりする。
    """

    @abstractmethod
    def save(self, data) -> str:
        """データを保存し、そのアーティファクトIDを返す。

        Args:
            data: 保存する任意のオブジェクト。

        Returns:
            str: 生成したアーティファクトID。
        """
        pass

    @abstractmethod
    def load(self, artifact_id):
        """アーティファクトIDからデータを読み込む。

        Args:
            artifact_id (str): 以前に保存したアーティファクトのID。

        Returns:
            保存時と同じオブジェクト。
        """
        pass
