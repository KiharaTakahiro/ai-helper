from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class SummarizeNode(Node):
    """テキストを要約するダミーノード。"""

    name = "summarize"
    tags = ["llm", "text"]

    inputs = ["text"]
    outputs = ["summary"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("text")
            text = artifact_repo.load(aid)
        except KeyError:
            text = ""
        summary = f"summary of: {text}"
        new_id = artifact_repo.save(summary)
        context.set_artifact("summary", new_id)
