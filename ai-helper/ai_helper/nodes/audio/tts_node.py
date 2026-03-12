from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class TTSNode(Node):
    """テキストを音声に変換するダミーノード。"""

    name = "tts"
    tags = ["audio", "tts"]

    inputs = ["text"]
    outputs = ["audio"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("text")
            text = artifact_repo.load(aid)
        except KeyError:
            text = ""
        audio = f"tts:{text}"
        new_id = artifact_repo.save(audio)
        context.set_artifact("audio", new_id)
