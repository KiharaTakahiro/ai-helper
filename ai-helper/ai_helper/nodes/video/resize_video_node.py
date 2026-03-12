from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class ResizeVideoNode(Node):
    """動画やフレームをリサイズするダミーノード。"""

    name = "resize_video"
    tags = ["video", "transform"]

    inputs = ["video"]
    outputs = ["resized"]

    def __init__(self, **config):
        self.config = config

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("video")
            video = artifact_repo.load(aid)
        except KeyError:
            video = None
        # サイズ変更は行わず、同じオブジェクトを返す
        new_id = artifact_repo.save(video)
        context.set_artifact("resized", new_id)
