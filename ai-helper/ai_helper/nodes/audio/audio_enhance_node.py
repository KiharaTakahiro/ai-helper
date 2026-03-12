from ai_helper.core.node.base_node import BaseNode


class AudioEnhanceNode(BaseNode):
    """音声を強化するダミーノード。

    実際の強化処理は後で実装する。
    """

    name = "audio_enhance"
    tags = ["audio", "enhance"]

    inputs = ["audio"]
    outputs = ["enhanced_audio"]

    def execute(self, context, runtime):
        # ダミーのオーディオを返す
        return {"enhanced_audio": b"dummy_audio_data"}
