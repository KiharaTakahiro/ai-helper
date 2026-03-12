from ai_helper.core.registry.registry import get_node_class


class NodeFactory:
    """PipelineDefinition の NodeDefinition から実インスタンスを生成する。

    `node_type` に対応するクラスをレジストリから取得し、
    `config` キーワード引数として渡してインスタンス化する。
    """

    def create(self, node_type: str, config: dict):
        """ノードを生成する。

        Args:
            node_type (str): 登録済みノード名。
            config (dict): コンストラクタへ渡す設定。

        Returns:
            Node: 生成されたノードオブジェクト。
        """
        node_cls = get_node_class(node_type)
        return node_cls(**config)
