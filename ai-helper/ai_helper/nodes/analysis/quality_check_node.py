from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class QualityCheckNode(Node):
    """品質チェック用のダミーノード。"""

    name = "quality_check"
    tags = ["analysis", "quality"]

    inputs = ["data"]
    outputs = ["quality_report"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("data")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save({"ok": True})
        context.set_artifact("quality_report", new_id)
