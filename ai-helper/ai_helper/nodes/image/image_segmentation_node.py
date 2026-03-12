from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class ImageSegmentationNode(Node):
    """画像セグメンテーションのダミーノード。"""

    name = "image_segmentation"
    tags = ["image", "segment"]

    inputs = ["image"]
    outputs = ["segments"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("image")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save([])
        context.set_artifact("segments", new_id)
