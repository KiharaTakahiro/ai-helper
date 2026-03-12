from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class ScriptNode(Node):
    """スクリプト生成のダミーノード。"""

    name = "script"
    tags = ["llm", "script"]

    inputs = ["prompt"]
    outputs = ["script_text"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("prompt")
            prompt = artifact_repo.load(aid)
        except KeyError:
            prompt = ""
        script = f"script based on {prompt}"
        new_id = artifact_repo.save(script)
        context.set_artifact("script_text", new_id)
