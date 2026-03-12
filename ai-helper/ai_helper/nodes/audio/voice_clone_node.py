from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class VoiceCloneNode(Node):
    """音声クローン処理のダミーノード。"""

    name = "voice_clone"
    tags = ["audio", "clone"]

    inputs = ["audio"]
    outputs = ["cloned_audio"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("audio")
            data = artifact_repo.load(aid)
        except KeyError:
            data = None
        new_id = artifact_repo.save(data)
        context.set_artifact("cloned_audio", new_id)
