from ai_helper.core.node.base_node import BaseNode


class VoiceCloneNode(BaseNode):
    """音声クローン処理のダミーノード。

    実際のクローン処理は後で実装する。
    """

    name = "voice_clone"
    tags = ["audio", "clone"]

    inputs = ["audio"]
    outputs = ["cloned_audio"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"cloned_audio": b"dummy_audio_data"}
