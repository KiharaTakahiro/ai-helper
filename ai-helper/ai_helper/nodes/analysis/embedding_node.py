from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class EmbeddingNode(Node):
    """埋め込み生成のダミーノード。"""

    name = "embedding"
    tags = ["analysis", "embedding"]

    inputs = ["text"]
    outputs = ["vector"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("text")
            text = artifact_repo.load(aid)
        except KeyError:
            text = ""
        # return fixed vector
        new_id = artifact_repo.save([0.0])
        context.set_artifact("vector", new_id)
