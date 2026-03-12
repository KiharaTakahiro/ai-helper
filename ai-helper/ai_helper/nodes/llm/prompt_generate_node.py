from ai_helper.core.node.base_node import BaseNode


class PromptGenerateNode(BaseNode):
    """プロンプト生成のダミーノード。

    実際のプロンプト生成処理は後で実装する。
    """

    name = "prompt_generate"
    tags = ["llm", "prompt"]

    inputs = ["text"]
    outputs = ["prompt"]

    def execute(self, context, runtime):
        # 実際の処理は後で実装
        return {"prompt": "dummy_text"}
