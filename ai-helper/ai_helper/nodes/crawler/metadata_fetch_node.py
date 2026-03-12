from ai_helper.core.node.base_node import BaseNode


class MetadataFetchNode(BaseNode):
    """メタデータを取得するダミーノード。

    実際の取得処理は後で実装する。
    """

    name = "metadata_fetch"
    tags = ["crawler", "metadata"]

    inputs = []
    outputs = ["metadata"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"metadata": {"dummy": "metadata"}}
