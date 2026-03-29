from ai_helper.core.registry import register_node
from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context


class VoiceNode(BaseNode):
    inputs = ["audio"]
    outputs = ["processed_audio"]

    def __init__(self, **config):
        self.config = config

    def execute(self, context: Context, artifact_repo):
        aid = context.get_artifact("audio")
        data = artifact_repo.load(aid)
        new = artifact_repo.save(data)
        context.set_artifact("processed_audio", new)


register_node("voice", VoiceNode)