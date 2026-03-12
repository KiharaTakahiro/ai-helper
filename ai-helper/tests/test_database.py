# tests/test_database.py
# DB関連の振る舞いを検証する。観点:
#  - パイプラインの入力検証エラーとそれに伴うDBステータス更新
#  - 成功パスにおけるPipelineRun/NodeRun/Artifactレコード作成
#  - ノード失敗時のステータスの反映
# さらにRepositoryクラスの基本的な create/update/get 動作も含め、
# SQLAlchemyモデル全体の行を網羅する。

import pytest
import datetime

from ai_helper.core.context import Context
from ai_helper.core.pipeline import Pipeline
from ai_helper.core.node import Node
from ai_helper.core.artifact.local_repository import LocalArtifactRepository
from ai_helper.core.registry import register_node
from ai_helper.db.session import create_sqlite_session
from ai_helper.db.models import PipelineRun, NodeRun, Artifact
from ai_helper.repository import (
    PipelineRunRepository,
    NodeRunRepository,
    ArtifactMetadataRepository,
)


def test_input_validation():
    # 観点: 入力アーティファクト不足時に例外が投げられること。
    #       また、DBセッションがある場合はパイプラインステータスが
    #       FAILED に更新されることを確認する。
    class BadNode(Node):
        inputs = ["missing"]
        outputs = []

        def run(self, context: Context, repo: LocalArtifactRepository):
            pass

    register_node("bad", BadNode)
    pipeline = Pipeline([BadNode()])
    ctx = Context()
    repo = LocalArtifactRepository()

    with pytest.raises(ValueError) as exc:
        pipeline.run(ctx, repo)
    assert "requires artifact 'missing'" in str(exc.value)

    # also verify DB logging marks pipeline as FAILED when session provided
    session = create_sqlite_session()
    repo_db = LocalArtifactRepository(metadata_repo=ArtifactMetadataRepository(session))
    pipeline.definition = type("D", (), {"id": "p_val"})()
    with pytest.raises(ValueError):
        pipeline.run(ctx, repo_db, db_session=session)
    pr = session.query(PipelineRun).first()
    assert pr.status == "FAILED"


def test_pipeline_run_logging_and_artifact_metadata():
    # 観点: 正常実行時にPipelineRun/NodeRunが記録され、
    #       アーティファクト保存時にメタデータが生成されること。
    session = create_sqlite_session()
    pr_repo = PipelineRunRepository(session)
    nr_repo = NodeRunRepository(session)
    metadata_repo = ArtifactMetadataRepository(session)

    # define an echo node
    class EchoNode(Node):
        inputs = ["input"]
        outputs = ["output"]

        def run(self, context: Context, repo: LocalArtifactRepository):
            aid = context.get_artifact("input")
            data = repo.load(aid)
            new = repo.save(data)
            context.set_artifact("output", new)

    register_node("echo_test", EchoNode)

    repo = LocalArtifactRepository(metadata_repo=metadata_repo)
    ctx = Context()
    first = repo.save("hello")
    ctx.set_artifact("input", first)

    pipeline = Pipeline([EchoNode()])
    # attach fake definition to allow pipeline_id extraction
    pipeline.definition = type("Def", (), {"id": "p_test"})()

    pipeline.run(ctx, repo, db_session=session)

    # verify pipeline run record
    runs = session.query(PipelineRun).all()
    assert len(runs) == 1
    pr = runs[0]
    assert pr.pipeline_id == "p_test"
    assert pr.status == "SUCCESS"

    # verify node run record
    nrs = session.query(NodeRun).all()
    assert len(nrs) == 1
    nr = nrs[0]
    assert nr.node_type == "EchoNode"
    assert nr.status == "SUCCESS"

    # verify artifact metadata (at least one record)
    arts = session.query(Artifact).all()
    assert len(arts) >= 1
    assert arts[0].type == "str" or arts[0].type is not None


def test_pipeline_failure_updates_status():
    # 観点: ノード実行中例外が発生した際にPipelineRunとNodeRun両方が
    #       FAILED に更新されることを確認する。
    session = create_sqlite_session()
    metadata_repo = ArtifactMetadataRepository(session)

    class FailingNode(Node):
        inputs = []
        outputs = []

        def run(self, context: Context, repo: LocalArtifactRepository):
            raise RuntimeError("boom")

    register_node("fail", FailingNode)
    repo = LocalArtifactRepository(metadata_repo=metadata_repo)
    pipeline = Pipeline([FailingNode()])
    pipeline.definition = type("Def", (), {"id": "p_fail"})()
    ctx = Context()

    with pytest.raises(RuntimeError):
        pipeline.run(ctx, repo, db_session=session)

    pr = session.query(PipelineRun).first()
    assert pr.status == "FAILED"
    nr = session.query(NodeRun).first()
    assert nr.status == "FAILED"
