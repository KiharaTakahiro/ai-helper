from ai_helper.core.node.base_node import BaseNode


class SimilarityCheckNode(BaseNode):
    """類似性チェックのダミーノード。

    実際の計算処理は後で実装する。
    """

    name = "similarity_check"
    tags = ["analysis", "similarity"]

    inputs = ["data"]
    outputs = ["similarity_score"]

    def execute(self, context, runtime):
        # ダミー値を返却
        return {"similarity_score": 0.0}
