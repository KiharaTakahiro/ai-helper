from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class Artifact:
    """
    Artifact data model.

    Represents the output of a Node execution.
    """

    id: str
    uri: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)