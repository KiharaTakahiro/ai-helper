"""旧来のノードレジストリ API を保持しつつ
内部で ``NodeRegistry`` クラスを利用するラッパーモジュール。"""

from ai_helper.core.registry.node_registry import NodeRegistry

# グローバルなシングルトンインスタンス
_global_registry = NodeRegistry()

# 旧 API としてエクスポートされていた辞書参照
NODE_REGISTRY = _global_registry._by_name


def register_node(name_or_cls, node_cls=None):
    """ノードクラスを登録するヘルパー関数。

    呼び出しは2通りサポート:

    ```python
    register_node("foo", FooNode)
    register_node(FooNode)
    ```
    """
    if node_cls is None:
        # 単一引数形式
        cls = name_or_cls
        _global_registry.register_node(cls)
    else:
        name = name_or_cls
        cls = node_cls
        _global_registry.register_node(cls, name=name)


def get_node_class(name: str):
    """登録済みノード名からクラスを取得する。

    Args:
        name (str): 登録時に使用した名前。

    Returns:
        Type[BaseNode]: 対応するクラス。
    """
    return _global_registry.get_node_by_name(name)

def unregister_node(name: str):
    """登録されたノードを名前で削除するヘルパー。

    旧スタイル API 互換として提供。
    """
    return _global_registry.unregister_node(name)
