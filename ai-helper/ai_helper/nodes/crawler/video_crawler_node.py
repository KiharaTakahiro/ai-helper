from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class VideoCrawlerNode(Node):
    """動画データを収集するダミーノード。"""

    name = "video_crawler"
    tags = ["crawler", "video"]

    outputs = ["video_list"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        # return empty list
        new_id = artifact_repo.save([])
        context.set_artifact("video_list", new_id)
