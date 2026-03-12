from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class AudioExtractNode(Node):
    """音声ファイルからトラックを抽出するダミーノード。"""

    name = "audio_extract"
    tags = ["audio", "input"]

    outputs = ["audio"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        # 何も読み込まず、空の文字列を保存
        new_id = artifact_repo.save("")
        context.set_artifact("audio", new_id)
