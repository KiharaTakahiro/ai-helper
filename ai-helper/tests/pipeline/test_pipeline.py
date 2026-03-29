from ai_helper.core.pipeline import Pipeline
from tests.fixtures.dummy_nodes import AddNode


class DummyDef:
    def __init__(self, node_id, node_type):
        self.node_id = node_id
        self.node_type = node_type
        self.config = {}
        self.depends_on = []


class DummyFactory:
    def create(self, node_type, config):
        return AddNode()


def test_pipeline_execution(context, artifact_repository):
    """
    観点:
        PipelineがNodeを正しい順序で実行し結果を生成すること
    """
    context.set_artifact("a", "1")
    context.set_artifact("b", "2")

    pd = type("PD", (), {})()
    pd.nodes = [DummyDef("n1", "add")]

    pipeline = Pipeline.from_definition(
        pd,
        node_factory=DummyFactory(),
        initial_artifacts={"a": None, "b": None},
    )

    pipeline.run(context, artifact_repository)

    assert context.get_artifact("result") == "3"