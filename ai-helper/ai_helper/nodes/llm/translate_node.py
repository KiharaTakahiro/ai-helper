from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class TranslateNode(Node):
    """テキストを翻訳するダミーノード。"""

    name = "translate"
    tags = ["llm", "text"]

    inputs = ["text"]
    outputs = ["translated"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("text")
            text = artifact_repo.load(aid)
        except KeyError:
            text = ""
        translated = f"translated:{text}"
        new_id = artifact_repo.save(translated)
        context.set_artifact("translated", new_id)
