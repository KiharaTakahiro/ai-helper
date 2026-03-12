from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class ImageEnhanceNode(Node):
    """画像を強化するダミーノード。"""

    name = "image_enhance"
    tags = ["image", "enhance"]

    inputs = ["image"]
    outputs = ["enhanced_image"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("image")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save(data)
        context.set_artifact("enhanced_image", new_id)
