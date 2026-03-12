from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class ImageCrawlerNode(Node):
    """画像データを収集するダミーノード。"""

    name = "image_crawler"
    tags = ["crawler", "image"]

    outputs = ["image_list"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        new_id = artifact_repo.save([])
        context.set_artifact("image_list", new_id)
