from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class PromptGenerateNode(Node):
    """プロンプト生成のダミーノード。"""

    name = "prompt_generate"
    tags = ["llm", "prompt"]

    inputs = ["text"]
    outputs = ["prompt"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("text")
            text = artifact_repo.load(aid)
        except KeyError:
            text = ""
        prompt = f"prompt for {text}"
        new_id = artifact_repo.save(prompt)
        context.set_artifact("prompt", new_id)
