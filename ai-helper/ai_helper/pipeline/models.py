from dataclasses import dataclass, field
from typing import List, Optional
import uuid


class NodeDefinition:
    """パイプライン構成の各ノードを表すクラス。

    新しい仕様では DAG をサポートするため以下の属性を持つ。

    Attributes:
        node_id (str): パイプライン内で一意な識別子。
        node_type (str): レジストリ登録名。
        config (dict): ノード初期化パラメータ。
        depends_on (list[str]): このノードが依存する他のノードID一覧。
        retry_count (int): 失敗時の再試行回数。
        retry_delay (float): 再試行の間隔（秒）。

    互換性のため旧仕様の ``type``/``order`` で初期化した場合も受け入れる。
    ``order`` は内部的に自動生成される ``node_id`` の元に使われるだけで、
    実行順序には影響しない。
    """

    def __init__(
        self,
        *,
        node_id: Optional[str] = None,
        node_type: Optional[str] = None,
        type: Optional[str] = None,
        config: Optional[dict] = None,
        order: Optional[int] = None,
        depends_on: Optional[List[str]] = None,
        retry_count: int = 0,
        retry_delay: float = 0.0,
        requires_gpu: bool = False,
    ):
        # backward compatibility: allow ``type`` and ``order`` parameters
        if node_type is None and type is not None:
            node_type = type
        if node_type is None:
            raise ValueError("node_type/type must be provided")

        self.node_type = node_type
        self.config = config or {}
        self.depends_on = depends_on or []
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.requires_gpu = requires_gpu
        # determine node_id
        if node_id is not None:
            self.node_id = node_id
        else:
            # if order provided use it to generate deterministic id for tests
            if order is not None:
                self.node_id = f"{self.node_type}_{order}"
            else:
                self.node_id = str(uuid.uuid4())
        # keep old attributes for compatibility tests
        self.type = node_type
        self.order = order or 0

    def __eq__(self, other):
        if not isinstance(other, NodeDefinition):
            return False
        return (
            self.node_id == other.node_id
            and self.node_type == other.node_type
            and self.config == other.config
            and self.depends_on == other.depends_on
            and self.retry_count == other.retry_count
            and self.retry_delay == other.retry_delay            and self.requires_gpu == other.requires_gpu        )

    def __repr__(self):
        return (
            f"NodeDefinition(node_id={self.node_id!r}, node_type={self.node_type!r}, "
            f"config={self.config!r}, depends_on={self.depends_on!r}, "
            f"retry_count={self.retry_count}, retry_delay={self.retry_delay}, "
            f"requires_gpu={self.requires_gpu})"
        )


    @classmethod
    def _snake(cls, name: str) -> str:
        """ Node class 名から registry lookup 用の type 名を生成する
        
         Example
           VideoInputNode -> video_input
           FrameExtractNode -> frame_extract
        
         NodeRegistry は snake_case の type 名でノードを検索するため
         YAML定義では class名ベースでも書けるようにしている
        """
        if name.endswith("Node"):
            name = name[: -len("Node")]
        import re

        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @classmethod
    def from_dict(cls, data: dict) -> "NodeDefinition":
        """辞書から NodeDefinition を生成するユーティリティ。

        Args:
            data (dict): ノード定義を表す辞書。例:
                {
                    "node_id": "node1",
                    "node_type": "typeA",
                    "config": {"param": 1},
                    "depends_on": ["node0"],
                    "retry_count": 3,
                    "retry_delay": 5.0,
                    "requires_gpu": True
                }
        """
        return cls(
            node_id=data.get("node_id"),
            node_type=cls._snake(data.get("node_type") or data.get("type")),
            config=data.get("config", {}),
            depends_on=data.get("depends_on", []),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 0.0),
            requires_gpu=data.get("requires_gpu", False),
        )

@dataclass
class PipelineDefinition:
    """ノードリストを持つパイプライン定義"""

    id: str
    nodes: List[NodeDefinition] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineDefinition":
        """辞書から PipelineDefinition を生成するユーティリティ。

        Args:
            data (dict): パイプライン定義を表す辞書。例:
                {
                    "id": "my_pipeline",
                    "nodes": [
                        {
                            "node_id": "node1",
                            "node_type": "typeA",
                            "config": {"param": 1},
                            "depends_on": []
                        },
                        ...
                    ]
                }
        """
        nodes = [
            NodeDefinition.from_dict(node_data) for node_data in data.get("nodes", [])
        ]
        return cls(id=data["id"], nodes=nodes)