from ai_helper.core.node.base_node import BaseNode


class SummarizeNode(BaseNode):
    """テキストを要約するダミーノード。

    実際の要約処理は後で実装する。
    """

    name = "summarize"
    tags = ["llm", "text"]

    inputs = ["text"]
    outputs = ["summary"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"summary": "dummy_text"}
