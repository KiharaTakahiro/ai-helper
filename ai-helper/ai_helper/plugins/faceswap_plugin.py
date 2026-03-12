from ai_helper.node.registry import register_node
from ai_helper.core.node import Node
from ai_helper.core.context import Context


class FaceSwapNode(Node):
    inputs = ["faces"]
    outputs = ["swapped"]

    def __init__(self, **config):
        self.config = config

    def run(self, context: Context, artifact_repo):
        # dummy implementation
        aid = context.get_artifact("faces")
        data = artifact_repo.load(aid)
        new = artifact_repo.save(data)
        context.set_artifact("swapped", new)


register_node("faceswap", FaceSwapNode)