from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class StyleTransferNode(Node):
    """スタイル変換のダミーノード。"""

    name = "style_transfer"
    tags = ["image", "style"]

    inputs = ["image"]
    outputs = ["styled_image"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("image")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save(data)
        context.set_artifact("styled_image", new_id)
