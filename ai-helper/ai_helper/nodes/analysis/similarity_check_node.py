from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class SimilarityCheckNode(Node):
    """類似性チェックのダミーノード。"""

    name = "similarity_check"
    tags = ["analysis", "similarity"]

    inputs = ["data"]
    outputs = ["similarity_score"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("data")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save(0.0)
        context.set_artifact("similarity_score", new_id)
