from ai_helper.core.node.base_node import BaseNode


class FaceSwapNode(BaseNode):
    """フレームリストを受け取り顔差し替え済みフレームを出力するノード（ダミー）。

    実際の処理は後で実装する。
    """

    name = "face_swap"
    tags = ["video", "faceswap"]

    inputs = ["frames"]
    outputs = ["swapped"]

    def execute(self, context, runtime):
        """ノード実行時に呼び出されるエントリポイント。

        ここではダミー出力を返すだけとし、
        実際の顔差し替え処理は後から実装する予定。

        Args:
            context: パイプライン実行コンテキスト。
            runtime: ランタイムあるいはArtifactRepository。

        Returns:
            dict: 出力アーティファクト名からダミー値へのマッピング。
        """
        # ダミーの戻り値を返す
        return {"swapped": b"dummy_swapped_data"}
