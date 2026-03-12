from enum import Enum


class ArtifactType(Enum):
    """アーティファクトの論理型を列挙する。

    ノードの ``inputs``/``outputs`` 定義で使用され、パイプライン全体
    の型整合性チェックに利用される。
    """

    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    FRAMES = "frames"
    TEXT = "text"
