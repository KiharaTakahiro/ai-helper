from ai_helper.core.node.base_node import BaseNode


class StyleTransferNode(BaseNode):
    """スタイル変換のダミーノード。

    実際のスタイル転送処理は後で実装する。
    """

    name = "style_transfer"
    tags = ["image", "style"]

    inputs = ["image"]
    outputs = ["styled_image"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"styled_image": b"dummy_image_data"}
