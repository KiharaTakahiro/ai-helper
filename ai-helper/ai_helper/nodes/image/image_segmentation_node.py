from ai_helper.core.node.base_node import BaseNode


class ImageSegmentationNode(BaseNode):
    """画像セグメンテーションのダミーノード。

    実際のセグメンテーション処理は後で実装する。
    """

    name = "image_segmentation"
    tags = ["image", "segment"]

    inputs = ["image"]
    outputs = ["segments"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"segments": b"dummy_image_data"}
