from ai_helper.core.node.base_node import BaseNode


class TTSNode(BaseNode):
    """テキストを音声に変換するダミーノード。

    実際のTTS処理は後で実装する。
    """

    name = "tts"
    tags = ["audio", "tts"]

    inputs = ["text"]
    outputs = ["audio"]

    def execute(self, context, runtime):
        # ダミーのオーディオデータを返す
        return {"audio": b"dummy_audio_data"}
