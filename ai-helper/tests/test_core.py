# tests/test_core.py
# このモジュールではパイプラインの基本動作に関する観点を検証する。
#  - ノードの登録とファクトリ動作
#  - 単一ノードパイプラインの実行とアーティファクトの受け渡し
#  - 複数ノードを連結した場合の順序・データ流れ
# これらを通じて `Pipeline`, `Context`, ノード基底クラスなどの
# コア機能が正常に動作することを確認し、結果的に関連コード行を網羅する。

from ai_helper.core.context import Context
from ai_helper.artifact.local_repository import LocalArtifactRepository
from ai_helper.node.registry import register_node
from ai_helper.pipeline.models import PipelineDefinition, NodeDefinition
from ai_helper.core.pipeline import Pipeline
from ai_helper.node.factory import NodeFactory
from ai_helper.core.node import Node


class EchoNode(Node):
    # support both list and dict forms; here we exercise typed dict
    inputs = {"input": "str"}
    outputs = {"output": "str"}

    def run(self, context: Context, repo: LocalArtifactRepository) -> None:
        artifact_id = context.get_artifact("input")
        data = repo.load(artifact_id) if artifact_id else None
        # explicitly pass type so metadata matches
        new_id = repo.save(data, type_="str")
        context.set_artifact("output", new_id)


# テスト用ノードを登録してファクトリが見つけられるようにする
register_node("echo", EchoNode)


def test_simple_pipeline():
    # 観点: ノード1つのパイプラインでContextとリポジトリ経由のデータ
    #       の流れが正しく行われるかを確認する。
    from ai_helper.db.session import create_sqlite_session
    from ai_helper.repository import ArtifactMetadataRepository

    session = create_sqlite_session()
    repo = LocalArtifactRepository(metadata_repo=ArtifactMetadataRepository(session))
    ctx = Context()

    first = repo.save("hello", type_="str")
    ctx.set_artifact("input", first)  # 入力を保存

    pd = PipelineDefinition(
        id="p1",
        nodes=[
            # order field is still accepted for backwards compatibility
            NodeDefinition(type="echo", config={}, order=1),
        ],
    )
    # build using new from_definition helper
    pipeline = Pipeline.from_definition(pd)
    pipeline.run(ctx, repo)

    out_id = ctx.get_artifact("output")
    assert out_id is not None
    assert repo.load(out_id) == "hello"


def test_pipeline_multiple_nodes():
    # 観点: 複数ノードが順番どおりに実行され、中間アーティファクトが
    #       正しく渡されること。挙動確認によりノード間のデータフロー
    #       ロジックとContextの管理がテストされる。
    repo = LocalArtifactRepository()
    ctx = Context()

    first = repo.save(1)
    ctx.set_artifact("input", first)

    class AddOneNode(Node):
        inputs = ["input"]
        outputs = ["intermediate"]

        def run(self, context: Context, repo: LocalArtifactRepository):
            aid = context.get_artifact("input")
            val = repo.load(aid)
            new = repo.save(val + 1)
            context.set_artifact("intermediate", new)

    class MultiplyNode(Node):
        inputs = ["intermediate"]
        outputs = ["output"]

        def run(self, context: Context, repo: LocalArtifactRepository):
            aid = context.get_artifact("intermediate")
            val = repo.load(aid)
            new = repo.save(val * 5)
            context.set_artifact("output", new)

    register_node("add1", AddOneNode)
    register_node("mul5", MultiplyNode)

    pd = PipelineDefinition(
        id="p2",
        nodes=[
            NodeDefinition(type="add1", config={}, order=1),
            NodeDefinition(type="mul5", config={}, order=2),
        ],
    )
    pipeline = Pipeline.from_definition(pd)
    pipeline.run(ctx, repo)

    out = ctx.get_artifact("output")
    assert repo.load(out) == (1 + 1) * 5
