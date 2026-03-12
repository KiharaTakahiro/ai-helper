from ai_helper.core.node.base_node import BaseNode


class AudioExtractNode(BaseNode):
    """音声ファイルからトラックを抽出するダミーノード。

    実際の抽出処理は後で実装する。
    """

    name = "audio_extract"
    tags = ["audio", "input"]
    outputs = ["audio"]

    def execute(self, context, runtime):
        """ダミーのオーディオデータを返す。

        Args:
            context: 実行コンテキスト。
            runtime: ランタイム／リポジトリオブジェクト。
        Returns:
            dict: 出力アーティファクト名からバイト列へのマッピング。
        """
        # 実際の処理は後で実装
        return {"audio": b"dummy_audio_data"}
