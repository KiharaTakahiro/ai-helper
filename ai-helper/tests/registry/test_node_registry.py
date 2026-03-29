from ai_helper.core.registry.node_registry import NodeRegistry
from ai_helper.core.node.base_node import BaseNode


class DummyNode(BaseNode):
    tags = ["test"]


def test_register_and_get():
    """
    観点:
        ノードが名前で正しく取得できること
    """
    registry = NodeRegistry()
    registry.register_node(DummyNode, name="dummy_node")

    node = registry.get_node_by_name("dummy_node")

    assert node is DummyNode


def test_get_by_tag():
    """
    観点:
        タグでノードを検索できること
    """
    registry = NodeRegistry()
    registry.register_node(DummyNode, name="dummy_node")

    nodes = registry.get_nodes_by_tag("test")

    assert DummyNode in nodes