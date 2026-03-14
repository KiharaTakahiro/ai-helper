from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class Artifact:
    """
    アーティファクトのデータモデル。

    Node 実行によって生成される成果物を表す。

    パイプラインでは Node が Artifact を生成し、
    次の Node がそれを入力として利用する。
    """

    id: str
    uri: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)