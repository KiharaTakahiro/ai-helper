from ai_helper.core.registry.node_registry import NodeRegistry
from ai_helper.core.node.base_node import BaseNode


class TestNode(BaseNode):
    tags = ["test"]


def test_register_and_get():
    """
    観点:
        ノードが名前で正しく取得できること
    """
    registry = NodeRegistry()
    registry.register_node(TestNode, name="test_node")

    node = registry.get_node_by_name("test_node")

    assert node is TestNode


def test_get_by_tag():
    """
    観点:
        タグでノードを検索できること
    """
    registry = NodeRegistry()
    registry.register_node(TestNode, name="test_node")

    nodes = registry.get_nodes_by_tag("test")

    assert TestNode in nodes