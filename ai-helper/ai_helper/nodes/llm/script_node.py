from ai_helper.core.node.base_node import BaseNode


class ScriptNode(BaseNode):
    """スクリプト生成のダミーノード。

    実際のスクリプト生成処理は後で実装する。
    """

    name = "script"
    tags = ["llm", "script"]

    inputs = ["prompt"]
    outputs = ["script_text"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"script_text": "dummy_text"}
