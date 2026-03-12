from ai_helper.core.node.base_node import BaseNode


class EmbeddingNode(BaseNode):
    """埋め込み生成のダミーノード。

    実際の埋め込み生成処理は後で実装する。
    """

    name = "embedding"
    tags = ["analysis", "embedding"]

    inputs = ["text"]
    outputs = ["vector"]

    def execute(self, context, runtime):
        # ダミーベクトルを返却
        return {"vector": [0.0]}
