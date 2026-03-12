from ai_helper.core.node.base_node import BaseNode


class ImageEnhanceNode(BaseNode):
    """画像を強化するダミーノード。

    実際の強化処理は後で実装する。
    """

    name = "image_enhance"
    tags = ["image", "enhance"]

    inputs = ["image"]
    outputs = ["enhanced_image"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"enhanced_image": b"dummy_image_data"}
