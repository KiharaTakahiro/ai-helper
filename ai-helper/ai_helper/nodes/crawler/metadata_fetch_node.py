from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class MetadataFetchNode(Node):
    """メタデータを取得するダミーノード。"""

    name = "metadata_fetch"
    tags = ["crawler", "metadata"]

    inputs = []
    outputs = ["metadata"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        new_id = artifact_repo.save({})
        context.set_artifact("metadata", new_id)
