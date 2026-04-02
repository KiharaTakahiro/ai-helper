import pytest
from ai_helper.core.executor import NodeExecutor
from tests.fixtures.dummy_nodes import AddNode, ErrorNode

def test_execute_success(context, artifact_repository):
    """
    観点:
        Nodeが正常に実行され、結果がContextに反映されること
    """
    context.set_artifact("a", "1")
    context.set_artifact("b", "2")

    executor = NodeExecutor(artifact_repository)

    executor.execute(AddNode(), context)

    assert context.get_artifact("result") == "3"


def test_execute_failure(context, artifact_repository):
    """
    観点:
        Node実行時の例外がそのまま呼び出し元に伝播すること
    """
    executor = NodeExecutor(artifact_repository)

    with pytest.raises(RuntimeError):
        executor.execute(ErrorNode(), context)

