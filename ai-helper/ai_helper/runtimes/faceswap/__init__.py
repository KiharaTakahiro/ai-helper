"""faceswap runtime connector.

ダミー実装として入力をそのまま返す。将来的には本物のモデル呼び出しを行う。
"""


class FaceSwapRuntime:
    """顔差し替え処理を外部モデルやツールへ委譲するランタイムクラス。"""

    @staticmethod
    def swap(frames, **config):
        """フレームリストに対して顔差し替えを行う処理。

        Args:
            frames: 任意のフレームリストオブジェクト。
            config: ノードから渡された構成パラメータ。
        Returns:
            処理済みフレームリスト（ここでは入力をそのまま返す）。
        """
        # TODO: 実際の顔差し替えロジックを実装
        return frames
