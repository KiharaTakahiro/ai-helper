from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class AudioEnhanceNode(Node):
    """音声を強化するダミーノード。"""

    name = "audio_enhance"
    tags = ["audio", "enhance"]

    inputs = ["audio"]
    outputs = ["enhanced_audio"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("audio")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        # そのまま返す
        new_id = artifact_repo.save(data)
        context.set_artifact("enhanced_audio", new_id)
