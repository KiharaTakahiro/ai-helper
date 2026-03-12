from ai_helper.core.node.base_node import BaseNode


class TranslateNode(BaseNode):
    """テキストを翻訳するダミーノード。

    実際の翻訳処理は後で実装する。
    """

    name = "translate"
    tags = ["llm", "text"]

    inputs = ["text"]
    outputs = ["translated"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"translated": "dummy_text"}
