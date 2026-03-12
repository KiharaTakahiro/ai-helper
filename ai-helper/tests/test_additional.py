# tests/test_additional.py（追加テスト集）
# 様々な補助的機能や例外ハンドリングを網羅するための観点テスト集。
# 各テストは特定の機能や境界条件を検証し、全体として100%カバレッジ
# を達成することを意図している。

import os
import uuid
import pytest
import datetime

from ai_helper.core.context import Context
from ai_helper.core.pipeline import Pipeline
from ai_helper.core.node import Node
from ai_helper.core.artifact.local_repository import LocalArtifactRepository
from ai_helper.core.artifact.repository import ArtifactRepository
from ai_helper.core.registry import register_node, get_node_class
from ai_helper.core.registry import NodeFactory
from ai_helper.pipeline.repository import PipelineRepository
from ai_helper.pipeline.models import PipelineDefinition, NodeDefinition
from ai_helper.config.settings import get_settings, Settings
from ai_helper.db.session import create_sqlite_session
from ai_helper.repository import (
    PipelineRunRepository,
    NodeRunRepository,
    ArtifactMetadataRepository,
    PipelineDefRepository,
    PipelineVersionRepository,
)
from ai_helper.db.models import PipelineRun, NodeRun, Artifact


# コンテキスト関連のテスト

# 観点: Context の基本操作 (格納、取得) と存在しないキーのエラー挙動を確認

def test_context_set_get_and_missing():
    ctx = Context()
    ctx.set_artifact("foo", "bar")
    assert ctx.get_artifact("foo") == "bar"
    with pytest.raises(KeyError):
        _ = ctx.get_artifact("nope")


# パイプラインリポジトリ関連

# 観点: 存在しないパイプラインID要求時にエラーが投げられること

def test_pipeline_repository_not_found():
    repo = PipelineRepository()
    with pytest.raises(ValueError):
        repo.get_pipeline("nonexistent")


# 観点: dataclass による等値比較が期待どおりに動作するか

def test_pipeline_definition_dataclass_eq():
    # NodeDefinition は手動で __eq__ を実装し、旧引数も受け付けるようになっている
    nd = NodeDefinition(type="a", config={"x":1}, order=0)
    pd1 = PipelineDefinition(id="p", nodes=[nd])
    pd2 = PipelineDefinition(id="p", nodes=[nd])
    assert pd1 == pd2


# ノードレジストリとファクトリ

# 観点: 未登録ノードアクセスでKeyError、登録・生成・設定渡しが機能すること

def test_node_registry_and_factory_errors():
    # 未登録時に KeyError が発生することを確認
    with pytest.raises(KeyError):
        get_node_class("does_not_exist")

    class Dummy(Node):
        def run(self, context: Context, artifact_repo):
            pass

    register_node("dummy", Dummy)
    factory = NodeFactory()
    inst = factory.create("dummy", {})
    assert isinstance(inst, Dummy)

    # 設定が正しく渡されることを確認
    class Cfg(Node):
        def __init__(self, foo, bar=2):
            self.foo = foo
            self.bar = bar

        def run(self, context: Context, artifact_repo):
            pass

    register_node("cfg", Cfg)
    keyed = factory.create("cfg", {"foo": 5, "bar": 7})
    assert keyed.foo == 5 and keyed.bar == 7


# 設定関連

# 観点: 設定取得ヘルパーが Settings インスタンスを返し初期値が正しいこと

def test_settings_default():
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.debug is True
    assert isinstance(s.base_artifact_dir, str)


# アーティファクトリポジトリ

# 観点: LocalArtifactRepository がファイル保存/読み込みを正しく行うか

def test_local_artifact_repository_basic(tmp_path):
    base = tmp_path / "art"
    repo = LocalArtifactRepository(base_dir=str(base))
    data = {"k": "v"}
    aid = repo.save(data)
    assert os.path.exists(base / (aid + ".bin"))
    loaded = repo.load(aid)
    assert loaded == data


# 観点: メタデータリポジトリの例外が保存処理に影響しないこと

def test_local_artifact_repository_metadata_failure(tmp_path):
    base = tmp_path / "meta"
    class BadMeta:
        def create(self, artifact_id, type_, repository_path):
            raise RuntimeError("fail meta")

    repo = LocalArtifactRepository(base_dir=str(base), metadata_repo=BadMeta())
    aid = repo.save(123)  # メタデータ例外は伝播しないこと
    assert aid is not None
    assert os.path.exists(base / (aid + ".bin"))


# リポジトリクラス

# 観点: ArtifactMetadataRepository の create/get 基本動作と存在しないIDハンドリング

def test_artifact_metadata_repository_create_and_get():
    session = create_sqlite_session()
    repo = ArtifactMetadataRepository(session)
    aid = str(uuid.uuid4())
    rec = repo.create(aid, "int", "/path")
    assert rec.id == aid
    got = repo.get(aid)
    assert got is not None and got.id == aid
    assert repo.get("nope") is None


# 観点: PipelineRunRepository, NodeRunRepository のエラー処理および
#       通常の作成・更新動作

def test_pipeline_node_run_repo_update_errors():
    session = create_sqlite_session()
    pr_repo = PipelineRunRepository(session)
    nr_repo = NodeRunRepository(session)

    # 存在しないレコードの更新
    with pytest.raises(ValueError):
        pr_repo.update_status("bad", "X")
    with pytest.raises(ValueError):
        nr_repo.update_status("bad", "X")

    # 通常の作成と更新
    pr = pr_repo.create("pid")
    pr_repo.update_status(pr.id, "RUNNING")
    assert pr_repo.session.get(PipelineRun, pr.id).status == "RUNNING"

    nr = nr_repo.create(pr.id, "nt")
    nr_repo.update_status(nr.id, "DONE")
    assert nr_repo.session.get(NodeRun, nr.id).status == "DONE"


# ノード実装

# 観点: VideoInputNode と FrameExtractNode の動作、及び
#       フレームノードの入力欠如例外

def test_video_and_frame_nodes(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    # 動画入力ノード
    vnode = __import__("ai_helper.nodes.video.video_input_node", fromlist=["VideoInputNode"]).VideoInputNode("path.mp4")
    ctx = Context()
    vnode.run(ctx, repo)
    vid = ctx.get_artifact("video")
    assert repo.load(vid) == "path.mp4"

    # フレーム抽出ノード成功ケース
    fnode = __import__("ai_helper.nodes.video.frame_extract_node", fromlist=["FrameExtractNode"]).FrameExtractNode()
    ctx2 = Context()
    ctx2.set_artifact("video", vid)
    fnode.run(ctx2, repo)
    frames_id = ctx2.get_artifact("frames")
    assert repo.load(frames_id) == ["path.mp4_frame_1", "path.mp4_frame_2"]

    # 入力欠如時に KeyError が発生すること
    ctx3 = Context()
    with pytest.raises(KeyError):
        fnode.run(ctx3, repo)


# パイプライン挙動

# 観点: DAG ソートとサイクル検出

def test_pipeline_dag_and_cycle():
    # 単純 DAG：no-op ノードを登録
    class Dummy(Node):
        inputs = []
        outputs = []
        def run(self, context: Context, repo):
            pass
    register_node("dummy", Dummy)
    nd1 = NodeDefinition(node_id="n1", node_type="dummy", config={}, depends_on=[])
    nd2 = NodeDefinition(node_id="n2", node_type="dummy", config={}, depends_on=["n1"])
    pd = PipelineDefinition(id="pdag", nodes=[nd1, nd2])
    pipeline = Pipeline.from_definition(pd)
    assert [n.definition.node_id for n in pipeline.nodes] == ["n1", "n2"]
    # サイクルがあれば例外が発生すること
    nd3 = NodeDefinition(node_id="a", node_type="dummy", config={}, depends_on=["b"])
    nd4 = NodeDefinition(node_id="b", node_type="dummy", config={}, depends_on=["a"])
    pd2 = PipelineDefinition(id="pcy", nodes=[nd3, nd4])
    with pytest.raises(ValueError):
        Pipeline.from_definition(pd2)

# 柔軟：プラグインからノードが自動登録されていること

def test_plugin_loading():
    # faceswap と voice プラグインがレジストリにより読み込まれているはず
    from ai_helper.core.registry import get_node_class
    # KeyError が発生しないことを確認
    get_node_class("faceswap")
    get_node_class("voice")

# キャッシュ挙動

def test_node_cache(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    # カウンターノード
    state = {"runs": 0}
    class CountNode(Node):
        inputs = []
        outputs = ["x"]
        def run(self, context: Context, repo):
            state["runs"] += 1
            aid = repo.save(1)
            context.set_artifact("x", aid)
    register_node("count", CountNode)
    pd = PipelineDefinition(id="pcache", nodes=[NodeDefinition(type="count", config={}, order=0)])
    pipeline = Pipeline.from_definition(pd)
    pipeline.run(ctx, repo)
    assert state["runs"] == 1
    # 同じ入力で再実行するとキャッシュされ（増加しない）
    pipeline.run(ctx, repo)
    assert state["runs"] == 1

# リトライ挙動

def test_node_retry(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    class Failing(Node):
        inputs = []
        outputs = ["o"]
        def __init__(self):
            self.attempts = 0
        def run(self, context: Context, repo):
            self.attempts += 1
            if self.attempts < 2:
                raise RuntimeError("boom")
            aid = repo.save("ok")
            context.set_artifact("o", aid)
    register_node("retry", Failing)
    nd = NodeDefinition(node_id="r1", node_type="retry", config={}, depends_on=[], retry_count=2, retry_delay=0)
    pd = PipelineDefinition(id="pretry", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    pipeline.run(ctx, repo)
    assert ctx.get_artifact("o") is not None

# GPUサポート: GPU必須のノードは利用不可時にスキップされるべき

def test_gpu_skip(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    class GpuNode(Node):
        inputs = []
        outputs = ["o"]
        def run(self, context: Context, repo):
            # 実行されないはず
            raise RuntimeError("ran despite GPU requirement")
    register_node("gpu", GpuNode)
    nd = NodeDefinition(node_id="g1", node_type="gpu", config={}, depends_on=[], requires_gpu=True)
    pd = PipelineDefinition(id="pgpu", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    # パイプラインで使うヘルパーはこの環境で False を返すはず
    from ai_helper.core.executor import _gpu_available
    assert not _gpu_available()
    pipeline.run(ctx, repo)
    # アーティファクトは設定されないはず
    with pytest.raises(KeyError):
        _ = ctx.get_artifact("o")

# NodeExecutor 単体利用

def test_node_executor_basic(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    class Echo(Node):
        inputs = []
        outputs = ["o"]
        def __init__(self, message):
            self.message = message
        def run(self, context: Context, repo):
            aid = repo.save(self.message)
            context.set_artifact("o", aid)
    register_node("echo", Echo)
    nd = NodeDefinition(node_id="e1", node_type="echo", config={"message": "hi"}, depends_on=[])
    from ai_helper.core.executor import NodeExecutor
    ne = NodeExecutor(repo)
    outs = ne.execute(nd, ctx)
    assert ctx.get_artifact("o") is not None
    assert outs["o"] == ctx.get_artifact("o")

# デバッグモード用ヘルパ

def test_pipeline_debug_helpers(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    class A(Node):
        inputs = []
        outputs = ["a"]
        def run(self, context: Context, repo):
            aid = repo.save("A")
            context.set_artifact("a", aid)
    class B(Node):
        inputs = ["a"]
        outputs = ["b"]
        def run(self, context: Context, repo):
            aid = repo.save("B")
            context.set_artifact("b", aid)
    register_node("A", A)
    register_node("B", B)
    n1 = NodeDefinition(node_id="n1", node_type="A", config={}, depends_on=[])
    n2 = NodeDefinition(node_id="n2", node_type="B", config={}, depends_on=["n1"])
    pipeline = Pipeline.from_definition(PipelineDefinition(id="pdbg", nodes=[n1, n2]))
    # ノード n1 を単独実行
    pipeline.run_node("n1", ctx, repo)
    assert ctx.get_artifact("a") is not None
    # n2 まで順次実行
    pipeline.run_until("n2", ctx, repo)
    assert ctx.get_artifact("b") is not None
    # ステップ実行
    ctx2 = Context()
    seq = list(pipeline.step_runner(ctx2, repo))
    assert seq[0][0] == "n1" and seq[1][0] == "n2"

# 並列実行: 依存関係のない 2 つの遅延ノード

def test_parallel_execution(tmp_path):
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    ctx = Context()
    import time
    class Slow(Node):
        inputs = []
        outputs = ["o"]
        def run(self, context: Context, repo):
            time.sleep(0.1)
            aid = repo.save(1)
            context.set_artifact("o", aid)
    register_node("slow1", Slow)
    register_node("slow2", Slow)
    pd = PipelineDefinition(
        id="ppar",
        nodes=[
            NodeDefinition(node_id="s1", node_type="slow1", config={}, depends_on=[]),
            NodeDefinition(node_id="s2", node_type="slow2", config={}, depends_on=[]),
        ],
    )
    pipeline = Pipeline.from_definition(pd)
    start = time.time()
    pipeline.run(ctx, repo)
    duration = time.time() - start
    # 両方0.1秒待機。並列なら0.2秒未満になるはず
    assert duration < 0.2

# アーティファクトのガーベジコレクション

def test_gc(tmp_path):
    base = tmp_path / "gc"
    session = create_sqlite_session()
    meta = ArtifactMetadataRepository(session)
    repo = LocalArtifactRepository(base_dir=str(base), metadata_repo=meta)
    aid = repo.save(123)
    # 手動でメタデータ日付を修正
    rec = meta.get(aid)
    rec.created_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=3600)
    session.commit()
    repo.gc(max_age_seconds=1)
    assert not os.path.exists(base / (aid + ".bin"))
    assert meta.get(aid) is None

# メトリクス記録

def test_node_metrics(tmp_path):
    session = create_sqlite_session()
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "m"), metadata_repo=ArtifactMetadataRepository(session))
    ctx = Context()
    class M(Node):
        inputs = []
        outputs = ["o"]
        def run(self, context: Context, repo):
            aid = repo.save(5)
            context.set_artifact("o", aid)
    register_node("met", M)
    pd = PipelineDefinition(id="pmet", nodes=[NodeDefinition(type="met", config={}, order=0)])
    pipeline = Pipeline.from_definition(pd)
    pipeline.run(ctx, repo, db_session=session)
    nr = session.query(NodeRun).first()
    assert nr.execution_time is not None
    assert nr.memory_usage is not None

def test_pipeline_run_without_definition():
    session = create_sqlite_session()
    class N(Node):
        def run(self, context: Context, artifact_repo):
            pass
    pipeline = Pipeline([N()])
    # definition 属性が無い場合
    ctx = Context()
    repo = LocalArtifactRepository(metadata_repo=ArtifactMetadataRepository(session))
    pipeline.run(ctx, repo, db_session=session)
    pr = session.query(PipelineRun).first()
    assert pr.pipeline_id == ""  # 空IDにフォールバック


# 観点: ノードが無いパイプラインがエラーを起こさず終了すること

def test_pipeline_no_nodes():
    # エラーにならないこと
    p = Pipeline([])
    p.run(Context(), LocalArtifactRepository())


# 観点: create_sqlite_session と get_session が有効なセッションを返す

def test_get_session_helper():
    # ヘルパーがテーブル付きの使用可能なセッションを返すことを確認
    sess = create_sqlite_session()
    assert sess is not None
    # get_session は同じ関数を呼ぶだけである
    from ai_helper.db.session import get_session

    sess2 = get_session()
    assert sess2 is not None


# 観点: 抽象クラスのパスを通し、未実装メソッドの `pass` を実行することで
#       その行をカバレッジに含める

def test_abstract_classes_covered():
    # ArtifactRepository の抽象メソッドには pass が含まれている
    class Impl(ArtifactRepository):
        def save(self, data):
            # 親クラスを呼んで pass 行を通す
            super().save(data)
            return "x"

        def load(self, aid):
            super().load(aid)
            return None

    impl = Impl()
    assert impl.save(1) == "x"
    assert impl.load("a") is None

    # Node 抽象 run の pass
    class ImplNode(Node):
        def run(self, context: Context, artifact_repo):
            super().run(context, artifact_repo)

    n = ImplNode()
    # run を呼ぶと基底の pass が実行されるはず
    n.run(Context(), LocalArtifactRepository())


# --- new feature tests -------------------------------------------------

def test_dag_cycle_detection():
    # 観点: 循環依存を含む定義で from_definition が例外を投げる
    from ai_helper.pipeline.models import NodeDefinition, PipelineDefinition
    from ai_helper.core.registry import NodeFactory

    nd1 = NodeDefinition(node_id="n1", node_type="dummy", config={}, depends_on=["n2"])
    nd2 = NodeDefinition(node_id="n2", node_type="dummy", config={}, depends_on=["n1"])
    pd = PipelineDefinition(id="p", nodes=[nd1, nd2])
    with pytest.raises(ValueError):
        Pipeline.from_definition(pd, node_factory=NodeFactory())


def test_cache_mechanism():
    # 観点: 同じ入力・設定のノードは2回目以降実行されない
    class CounterNode(Node):
        inputs = {}
        outputs = {"out": "Any"}

        def __init__(self):
            self.count = 0

        def run(self, context: Context, repo: LocalArtifactRepository):
            self.count += 1
            aid = repo.save("x", type_="Any")
            context.set_artifact("out", aid)

    register_node("counter", CounterNode)
    from ai_helper.pipeline.models import NodeDefinition, PipelineDefinition
    nd = NodeDefinition(node_id="c", node_type="counter", config={}, depends_on=[])
    pd = PipelineDefinition(id="p", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    ctx = Context()
    repo = LocalArtifactRepository()
    pipeline.run(ctx, repo)
    first_id = ctx.get_artifact("out")
    # 同じパイプラインとコンテキストで再実行
    pipeline.run(ctx, repo)
    second_id = ctx.get_artifact("out")
    assert first_id == second_id


def test_retry_logic():
    # 観点: 失敗ノードがリトライされ成功すること
    class FlakyNode(Node):
        inputs = {}
        outputs = {"out": "Any"}

        def __init__(self):
            self.called = 0

        def run(self, context: Context, repo: LocalArtifactRepository):
            self.called += 1
            if self.called < 2:
                raise RuntimeError("bad")
            aid = repo.save("v", type_="Any")
            context.set_artifact("out", aid)

    register_node("flaky", FlakyNode)
    from ai_helper.pipeline.models import NodeDefinition, PipelineDefinition
    nd = NodeDefinition(node_id="f", node_type="flaky", config={}, depends_on=[], retry_count=1, retry_delay=0)
    pd = PipelineDefinition(id="p", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    ctx = Context()
    repo = LocalArtifactRepository()
    pipeline.run(ctx, repo)
    assert ctx.get_artifact("out") is not None


def test_parallel_execution_time():
    # 観点: 依存関係のないノードは並列実行されて所要時間が短縮される
    import time

    class SleepNode(Node):
        inputs = {}
        outputs = {"o": "Any"}

        def __init__(self, delay):
            self.delay = delay

        def run(self, context: Context, repo: LocalArtifactRepository):
            time.sleep(self.delay)
            aid = repo.save("x", type_="Any")
            context.set_artifact("o", aid)

    register_node("sleep", SleepNode)
    from ai_helper.pipeline.models import NodeDefinition, PipelineDefinition
    nd1 = NodeDefinition(node_id="a", node_type="sleep", config={"delay": 0.1}, depends_on=[])
    nd2 = NodeDefinition(node_id="b", node_type="sleep", config={"delay": 0.1}, depends_on=[])
    pd = PipelineDefinition(id="p", nodes=[nd1, nd2])
    pipeline = Pipeline.from_definition(pd)
    ctx = Context()
    repo = LocalArtifactRepository()
    start = time.perf_counter()
    pipeline.run(ctx, repo)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.18  # 2つの待機が並列のため


def test_metrics_recorded():
    # 観点: NodeRun に execution_time と memory_usage が保存される
    session = create_sqlite_session()
    metadata = ArtifactMetadataRepository(session)
    class Simple(Node):
        inputs = {}
        outputs = {"out": "Any"}
        def run(self, context: Context, repo: LocalArtifactRepository):
            aid = repo.save(1, type_="Any")
            context.set_artifact("out", aid)
    register_node("simple", Simple)
    nd = NodeDefinition(node_id="s", node_type="simple", config={}, depends_on=[])
    pd = PipelineDefinition(id="p", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    ctx = Context()
    repo = LocalArtifactRepository(metadata_repo=metadata)
    pipeline.run(ctx, repo, db_session=session)
    nr = session.query(NodeRun).first()
    assert nr.execution_time is not None
    assert nr.memory_usage is not None


def test_artifact_type_validation():
    # 観点: 入力アーティファクトの型が定義と一致しないと例外
    repo = LocalArtifactRepository()
    ctx = Context()
    aid = repo.save("x", type_="StrType")
    ctx.set_artifact("input", aid)
    class TypeNode(Node):
        inputs = {"input": "Other"}
        outputs = {"out": "Any"}
        def run(self, context: Context, repo: LocalArtifactRepository):
            pass
    register_node("type", TypeNode)
    nd = NodeDefinition(node_id="t", node_type="type", config={}, depends_on=[])
    pd = PipelineDefinition(id="p", nodes=[nd])
    pipeline = Pipeline.from_definition(pd)
    with pytest.raises(TypeError):
        pipeline.run(ctx, repo)


def test_garbage_collection(tmp_path):
    # 観点: gc() が一定期間より古いアーティファクトを削除する
    repo = LocalArtifactRepository(base_dir=str(tmp_path / "store"))
    aid1 = repo.save("a", type_="Any")
    time.sleep(0.01)
    aid2 = repo.save("b", type_="Any")
    # ごく短い期間より古いアーティファクトを削除
    repo.gc(max_age_seconds=0)
    assert os.path.exists(repo._path(aid2))
    assert not os.path.exists(repo._path(aid1))


def test_pipeline_versioning():
    # 観点: パイプラインとバージョン情報がDBに記録・取得できる
    session = create_sqlite_session()
    prepo = PipelineDefRepository(session)
    pvrepo = PipelineVersionRepository(session)
    p = prepo.create_pipeline("myp")
    pv = pvrepo.create_version(p.id, "v1", {"foo": "bar"})
    latest = pvrepo.get_latest(p.id)
    assert latest is not None and latest.version == "v1"


def test_plugin_loading():
    # 観点: plugins/sample_plugin が自動登録されている
    from ai_helper.core.registry import get_node_class
    cls = get_node_class("plugin_node")
    assert cls.__name__ == "PluginNode"

