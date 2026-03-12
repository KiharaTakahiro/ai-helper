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
            and self.retry_delay == other.retry_delay
        )

    def __repr__(self):
        return (
            f"NodeDefinition(node_id={self.node_id!r}, node_type={self.node_type!r}, "
            f"config={self.config!r}, depends_on={self.depends_on!r}, "
            f"retry_count={self.retry_count}, retry_delay={self.retry_delay})"
        )


@dataclass
class PipelineDefinition:
    """ノードリストを持つパイプライン定義"""

    id: str
    nodes: List[NodeDefinition] = field(default_factory=list)