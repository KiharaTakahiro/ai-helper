from ai_helper.core.registry import register_node
from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository


class PluginNode(BaseNode):
    inputs = {}
    outputs = {}

    def execute(self, context: Context, artifact_repo: ArtifactRepository):
        # no op plugin
        pass


register_node("plugin_node", PluginNode)
