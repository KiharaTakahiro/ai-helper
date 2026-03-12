from ai_helper.core.node.base_node import BaseNode


class ImageCrawlerNode(BaseNode):
    """画像データを収集するダミーノード。

    実際のクローリング処理は後で実装する。
    """

    name = "image_crawler"
    tags = ["crawler", "image"]

    outputs = ["image_list"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"image_list": ["dummy_url"]}
