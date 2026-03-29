from ai_helper.core.registry import register_node
from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context

# runtime を呼び出すためにインポート（スタブ）
from ai_helper.runtimes.faceswap import FaceSwapRuntime


class FaceSwapNode(BaseNode):
    """フレームリストを受け取り顔差し替え済みフレームを出力するノード。"""

    name = "faceswap"
    tags = ["video", "faceswap"]

    inputs = ["frames"]
    outputs = ["swapped"]

    def __init__(self, **config):
        self.config = config

    def execute(self, context: Context, artifact_repo):
        aid = context.get_artifact("frames")
        frames = artifact_repo.load(aid)
        swapped = FaceSwapRuntime.swap(frames, **self.config)
        new_id = artifact_repo.save(swapped)
        context.set_artifact("swapped", new_id)


register_node("faceswap", FaceSwapNode)