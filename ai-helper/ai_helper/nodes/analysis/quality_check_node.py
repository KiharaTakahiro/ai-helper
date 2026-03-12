from ai_helper.core.node.base_node import BaseNode


class QualityCheckNode(BaseNode):
    """品質チェック用のダミーノード。

    実際の品質判定処理は後で実装する。
    """

    name = "quality_check"
    tags = ["analysis", "quality"]

    inputs = ["data"]
    outputs = ["quality_report"]

    def execute(self, context, runtime):
        # ダミー結果を返却
        return {"quality_report": {"ok": True}}
