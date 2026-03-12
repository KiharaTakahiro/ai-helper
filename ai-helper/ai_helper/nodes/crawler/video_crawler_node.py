from ai_helper.core.node.base_node import BaseNode


class VideoCrawlerNode(BaseNode):
    """動画データを収集するダミーノード。

    実際のクローリング処理は後で実装する。
    """

    name = "video_crawler"
    tags = ["crawler", "video"]

    outputs = ["video_list"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"video_list": ["dummy_url"]}
