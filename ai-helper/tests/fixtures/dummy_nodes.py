from ai_helper.core.node.base_node import BaseNode


class AddNode(BaseNode):
    """2つの値を加算するシンプルなノード（正常系テスト用）"""
    inputs = ["a", "b"]
    outputs = ["result"]

    def run(self, context, repo):
        result = int(context.get_artifact("a")) + int(context.get_artifact("b"))
        context.set_artifact("result", str(result))


class ErrorNode(BaseNode):
    """必ず失敗するノード（例外処理テスト用）"""

    def run(self, context, repo):
        raise RuntimeError("意図的なエラー")


class RetryNode(BaseNode):
    """1回失敗して次に成功するノード（リトライテスト用）"""

    outputs = ["x"]

    def __init__(self):
        super().__init__()
        self.count = 0

    def run(self, context, repo):
        self.count += 1
        if self.count == 1:
            raise RuntimeError("初回失敗")
        context.set_artifact("x", "ok")