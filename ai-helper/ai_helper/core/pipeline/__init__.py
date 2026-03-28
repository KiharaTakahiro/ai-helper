"""
Pipeline execution engine.

Pipeline は Node の DAG (Directed Acyclic Graph) を表す。

構造

Pipeline
   ↓
Node
   ↓
Artifact

Node は Artifact を入力として受け取り
新しい Artifact を生成する。

Pipeline は

1 依存関係解決
2 実行順序決定
3 Node実行

を管理する。
"""

import datetime
import hashlib
import json
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository
from ai_helper.core.node import Node

logger = logging.getLogger(__name__)

def _topological_sort(deps: Dict[str, List[str]]) -> List[str]:
    """依存関係グラフをトポロジカルソートする。

    Args:
        deps: node_id -> list of node_ids it depends on
    Returns:
        Sorted list of node_ids.
    Raises:
        ValueError: 循環依存が検出された場合。
    """
    result = []
    temp_marks = set()
    perm_marks = set()

    def visit(n):
        if n in perm_marks:
            return
        if n in temp_marks:
            raise ValueError(f"cycle detected at node {n}")
        temp_marks.add(n)
        for m in deps.get(n, []):
            visit(m)
        temp_marks.remove(n)
        perm_marks.add(n)
        result.append(n)

    # iterate in insertion order of deps dict, which matches pipeline definition order
    for node in deps:
        if node not in perm_marks:
            visit(node)
    # the algorithm above already appends nodes in a valid order (dependencies first),
    # so no need to reverse the result. Reversing caused nodes without dependencies to
    # appear in reverse of their original order.
    return result


class Pipeline:
    """パイプライン処理を担当するクラス。

    ``nodes`` はトポロジカル順に並んだ ``Node`` インスタンスのリスト。

    ``cache`` は NodeCache のための辞書で、キー -> outputs となる。
    """

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.cache = {}
        # attach id map for convenience (node.definition.node_id -> node)
        self._node_map = {getattr(n, 'definition', None).node_id: n for n in nodes if hasattr(n, 'definition')}

    @classmethod
    def from_definition(cls, pd, node_factory=None, initial_artifacts: Dict[str, str] = None):
        """
        PipelineDefinition（設定データ）から実行可能なPipelineインスタンスを生成する。

        主な処理内容：
        - ノード間の依存関係（DAG）を構築
        - トポロジカルソートにより実行順序を決定
        - NodeFactoryを用いてノードをインスタンス化
        - 入出力の簡易的な静的検証を実施
        """
        from ai_helper.core.registry.factory import NodeFactory

        # Node生成用のFactory（未指定ならデフォルト）を使用
        node_factory = node_factory or NodeFactory()
        # -------------------------
        # 依存関係マップの構築
        # -------------------------
        deps = {}

        # definitionからdepends_onを取得
        for idx, d in enumerate(pd.nodes):
            deps[d.node_id] = list(d.depends_on)

        # depends_on未指定のノードは直前ノードに依存させる（順次実行のため）
        for idx, d in enumerate(pd.nodes):
            if idx > 0 and not deps.get(d.node_id):
                prev = pd.nodes[idx - 1]
                deps[d.node_id].append(prev.node_id)
        # -------------------------
        # 実行順序の決定（DAGソート）
        # -------------------------
        sorted_ids = _topological_sort(deps)
        
        # -------------------------
        # ノードの生成と検証
        # -------------------------
        nodes = []
        produced_outputs = {}
        for nid in sorted_ids:
            # node_idからdefinitionを取得
            d = next(filter(lambda x: x.node_id == nid, pd.nodes))
            # Nodeインスタンス生成
            node = node_factory.create(d.node_type, d.config)
            # definitionを保持（実行時参照用)
            node.definition = d
            nodes.append(node)

            # -------------------------
            # 入力検証（静的チェック）
            # -------------------------
            inputs = []
            if hasattr(node, 'inputs'):
                if isinstance(node.inputs, dict):
                    inputs = list(node.inputs.keys())
                else:
                    inputs = list(node.inputs)

            for inp in inputs:
                if initial_artifacts is not None:
                    # 外部から渡される入力を許可
                    if inp in initial_artifacts:
                        # 型チェック（定義がある場合）
                        exp = node.inputs[inp] if isinstance(node.inputs, dict) else None
                        if exp and initial_artifacts[inp] != exp:
                            logger.error(f"initial artifact '{inp}' type mismatch: {initial_artifacts[inp]} が {exp}と異なります")
                            raise TypeError(f"initial artifact '{inp}' type mismatch: {initial_artifacts[inp]} が {exp}と異なります")
                        continue
                    
                    # 型チェック（定義がある場合）
                    if inp not in produced_outputs:
                        logger.error(f"Input artifact '{inp}' のノードID: '{nid}' の型が不一致")
                        raise ValueError(f"Input artifact '{inp}' のノードID: '{nid}' の型が不一致")

            # -------------------------
            # 出力の記録
            # -------------------------
            outputs = []
            if hasattr(node, 'outputs'):
                if isinstance(node.outputs, dict):
                    outputs = list(node.outputs.keys())
                else:
                    outputs = list(node.outputs)
            for out in outputs:
                produced_outputs[out] = True
        # -------------------------
        # Pipeline生成
        # -------------------------
        pipeline = cls(nodes)
        pipeline.definition = pd
        return pipeline

    def _compute_cache_key(self, node: Node, context: Context):
        # build key components
        nid = getattr(node, 'definition', None).node_type if hasattr(node, 'definition') else node.__class__.__name__
        # inputs: artifact ids sorted by name
        inp_map = {}
        if hasattr(node, 'inputs'):
            if isinstance(node.inputs, dict):
                keys = node.inputs.keys()
            else:
                keys = node.inputs
            for k in keys:
                if k in context.artifacts:
                    inp_map[k] = context.artifacts[k]
        inp_tuple = tuple(sorted(inp_map.items()))
        # config hash
        cfg = getattr(node, 'definition', None).config if hasattr(node, 'definition') else {}
        cfg_json = json.dumps(cfg, sort_keys=True)
        cfg_hash = hashlib.sha256(cfg_json.encode()).hexdigest()
        return (nid, inp_tuple, cfg_hash)

    def _validate_types(self, node: Node, context: Context, artifact_repo: ArtifactRepository):
        # check input artifact types
        if isinstance(node.inputs, dict):
            if getattr(artifact_repo, 'metadata_repo', None) is not None:
                for name, expected in node.inputs.items():
                    aid = context.artifacts.get(name)
                    if aid is None:
                        raise ValueError(f"Node {node.definition.node_id} missing input '{name}'")
                    rec = artifact_repo.metadata_repo.get(aid)
                    if rec and rec.type != expected:
                        raise TypeError(f"artifact '{name}' has type {rec.type} but node expects {expected}")
        # outputs will be checked after run

    def _check_output_types(self, node: Node, context: Context, artifact_repo: ArtifactRepository):
        if isinstance(node.outputs, dict):
            if getattr(artifact_repo, 'metadata_repo', None) is not None:
                for name, expected in node.outputs.items():
                    aid = context.artifacts.get(name)
                    if aid is None:
                        raise ValueError(f"Node {node.definition.node_id} failed to produce output '{name}'")
                    rec = artifact_repo.metadata_repo.get(aid)
                    if rec and rec.type != expected:
                        raise TypeError(f"output artifact '{name}' has type {rec.type} but node declared {expected}")

    def run(
        self,
        context: Context,
        artifact_repo: ArtifactRepository,
        db_session=None,
    ):
        """DAG 対応バージョンの run メソッド。

        - 依存関係を元に並列実行
        - キャッシュチェック
        - リトライ
        - タイプ検証
        - メトリクス収集
        """
        logger.info("[開始] パイプラインの実行")
        pr_repo = None
        nr_repo = None
        
        # DB セッションが提供されている場合はパイプラインランとノードランのレコードを作成して状態管理する
        if db_session is not None:
            from ai_helper.repository import PipelineRunRepository, NodeRunRepository
            logger.info("DBセッションが提供されているため、パイプラインランとノードランのレコードを作成して状態管理を行う")
            pr_repo = PipelineRunRepository(db_session)
            nr_repo = NodeRunRepository(db_session)
            pipeline_id = getattr(self, "definition", None)
            pipeline_id = getattr(pipeline_id, "id", None) or ""
            pr = pr_repo.create(pipeline_id)
            pr_repo.update_status(pr.id, "RUNNING")

        # definition に定義された depends_on をもとに、
        # ノード間の依存関係マップ（DAG）を構築する
        #
        # deps の形式：
        #   deps[node_id] = [依存ノードID, ...]
        #
        # 例：
        #   deps = {
        #       "step1": [],
        #       "step2": ["step1"],
        #   }
        #
        # → step1 完了後に step2 が実行される
        deps = {}

        # self.nodes の順序を維持しつつ依存関係を構築
        for idx, node in enumerate(self.nodes):
            nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None
            if nid is not None:
                # depends_on をそのままコピー（空リストも含む）
                deps[nid] = list(getattr(node.definition, 'depends_on', []))

        # depends_on が空のノードに対しては、
        # 前のノードへの依存関係を暗黙的に追加する
        #
        # これにより、単純なリスト形式で定義されたパイプラインでも
        # 上から順番に実行されるようにする（並列実行を防ぐ）
        # 注意：
        # depends_on を指定しない場合、
        # ノードは自動的に直列実行される。
        # 並列にしたい場合は依存関係を明示すること。
        # 先頭ノードを並列としたい場合は、ダミーノードを使用して並列化させること
        for idx, node in enumerate(self.nodes):
            nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None
            if nid is None:
                continue
            if not deps.get(nid) and idx > 0:
                prev = self.nodes[idx - 1]
                prev_id = getattr(prev, 'definition', None).node_id if hasattr(prev, 'definition') else None
                if prev_id is not None:
                    deps[nid].append(prev_id)

        logger.info(f"ノード間の依存関係: {deps}")

        # 実行中ノード
        in_progress = {}
        # 完了ノード
        completed = set()
        # 並列実行時の排他制御
        lock = threading.Lock()

        # Node の実行ロジックを担当する Executor を生成
        # （リトライ、ログ、メトリクス収集などはここで処理される）
        from ai_helper.core.executor import NodeExecutor
        node_executor = NodeExecutor(artifact_repo, db_session=db_session)

        # ノード1つ分の実行処理
        # ThreadPoolExecutor から呼ばれ、並列実行される可能性があるため、ローカル変数で必要なリポジトリをキャプチャして渡す 
        def _execute(node: Node):
            nonlocal pr_repo, nr_repo, pr
            # ノードIDを取得（definitionが無い場合はクラス名を使用）
            nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else node.__class__.__name__

            # 実際のノード処理は NodeExecutor に委譲する
            outputs = node_executor.execute(node, context, pipeline_run_id=pr.id if pr_repo is not None else None)
            with lock:
                # 完了したノードを記録（並列実行のため排他制御）
                completed.add(nid)
            return outputs

        # 並列実行用のスレッドプールを生成
        executor = ThreadPoolExecutor()
        # 実行中タスク（Future）とノードの対応を保持
        futures = {}

        # メインの実行ループ
        # すべてのノードが完了するまで繰り返す
        try:
            while len(completed) < len(self.nodes):

                # 実行可能なノードをスケジューリング
                for node in self.nodes:
                    nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None

                    # 既に完了済み、または実行中のノードはスキップ
                    if nid in completed or nid in in_progress:
                        logger.debug(f"ノード '{nid}' はすでに完了済みまたは実行中のためスキップ")
                        continue

                    # 依存ノードがすべて完了しているかチェック 
                    deps_ok = all(d in completed for d in deps.get(nid, []))
                    if not deps_ok:
                        logger.debug(f"ノード '{nid}' は依存ノードが未完了のためスキップ (依存: {deps.get(nid, [])}, 完了: {completed})")
                        continue
                    
                    # NOTE: キャッシュ利用は高速化には便利な一方ノードの副作用を考慮する必要がある
                    # 現時点で考慮できていないが、今後ノードにキャッシュを使用してよいかのフラグを持つなど対応が必要

                    # キャッシュ確認（同じ入力なら再実行しない）
                    key = self._compute_cache_key(node, context)
                    if key in self.cache:
                        # キャッシュから結果を復元
                        for name, aid in self.cache[key].items():
                            logger.info(f"ノード '{nid}' はキャッシュヒットのため再実行せず、出力 '{name}' をアーティファクトID '{aid}' で復元")
                            context.set_artifact(name, aid)
                        completed.add(nid)
                        continue

                    # ノードを並列実行としてスケジュール
                    logger.info(f"ノード '{nid}' をスケジューリング（依存関係: {deps.get(nid, [])}）")
                    fut = executor.submit(_execute, node)

                    # 実行中タスクとして管理
                    futures[fut] = node
                    in_progress[nid] = fut

                # 実行可能なノードが無いのに未完了ノードがある場合
                # → 循環依存の可能性
                if not futures and len(completed) < len(self.nodes):
                     logger.error("実行可能なノードがないのに未完了ノードが存在します。循環依存の可能性があります。")
                     raise RuntimeError("実行可能なノードがないが未完了ノードが存在します。循環依存の可能性があります。")
 
                # 少なくとも1つのノードが完了するまで待機
                if futures:
                    from concurrent.futures import wait, FIRST_COMPLETED

                    done_set, _ = wait(futures.keys(), return_when=FIRST_COMPLETED)

                    for fut in done_set:
                        node = futures.pop(fut)
                        nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None

                        # 実行中リストから削除
                        in_progress.pop(nid, None)
                        # 実行結果取得（例外もここで発生する）
                        outputs = fut.result()
                        # 結果をキャッシュに保存
                        key = self._compute_cache_key(node, context)
                        self.cache[key] = outputs
        except Exception:
            # パイプライン全体を失敗状態にする
            if pr_repo is not None:
                pr_repo.update_status(pr.id, "FAILED", finished_at=datetime.datetime.now(datetime.UTC))
            raise
        finally:
            # パイプライン全体を失敗状態にする
            executor.shutdown(wait=False)
            logger.info("[完了] パイプラインの実行")