"""Core pipeline package containing Pipeline implementation."""

import datetime
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tracemalloc
from typing import Dict, List

from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository
from ai_helper.core.node import Node


# GPU availability helper (same logic as in node_executor for consistency)
def _gpu_available():
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


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

    for node in deps:
        if node not in perm_marks:
            visit(node)
    return list(reversed(result))


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
        """PipelineDefinition から Pipeline インスタンスを作成する。

        トポロジカルソートと簡単な検証を行う。
        """
        from ai_helper.core.registry.factory import NodeFactory

        node_factory = node_factory or NodeFactory()
        # build graph
        deps = {}
        for d in pd.nodes:
            deps[d.node_id] = list(d.depends_on)
        sorted_ids = _topological_sort(deps)
        # instantiate nodes in order
        nodes = []
        produced_outputs = {}
        for nid in sorted_ids:
            d = next(filter(lambda x: x.node_id == nid, pd.nodes))
            node = node_factory.create(d.node_type, d.config)
            node.definition = d
            nodes.append(node)
            # basic static validation: check that inputs either come from previous nodes or
            # appear in initial_artifacts (if provided)
            inputs = []
            if hasattr(node, 'inputs'):
                if isinstance(node.inputs, dict):
                    inputs = list(node.inputs.keys())
                else:
                    inputs = list(node.inputs)
            for inp in inputs:
                if initial_artifacts is not None:
                    if inp in initial_artifacts:
                        # type check if typing information present
                        exp = node.inputs[inp] if isinstance(node.inputs, dict) else None
                        if exp and initial_artifacts[inp] != exp:
                            raise TypeError(f"initial artifact '{inp}' type mismatch: {initial_artifacts[inp]} != {exp}")
                        continue
                    if inp not in produced_outputs:
                        raise ValueError(f"Input artifact '{inp}' for node '{nid}' is not produced by any preceding node or provided initial artifacts")
                # if no initial_artifacts provided we skip existence check - assume runtime context will supply
            # record outputs
            outputs = []
            if hasattr(node, 'outputs'):
                if isinstance(node.outputs, dict):
                    outputs = list(node.outputs.keys())
                else:
                    outputs = list(node.outputs)
            for out in outputs:
                produced_outputs[out] = True
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
        # optional repositories
        pr_repo = None
        nr_repo = None
        if db_session is not None:
            from ai_helper.repository import PipelineRunRepository, NodeRunRepository

            pr_repo = PipelineRunRepository(db_session)
            nr_repo = NodeRunRepository(db_session)
            pipeline_id = getattr(self, "definition", None)
            pipeline_id = getattr(pipeline_id, "id", None) or ""
            pr = pr_repo.create(pipeline_id)
            pr_repo.update_status(pr.id, "RUNNING")

        # if any node lacks a definition we don't know dependencies or ids,
        # fall back to original sequential behavior for compatibility.
        if not all(hasattr(n, 'definition') for n in self.nodes):
            last_node_run = None
            try:
                for node in self.nodes:
                    # validate inputs (old style)
                    for inp in getattr(node, "inputs", []):
                        if inp not in context.artifacts:
                            raise ValueError(
                                f"Node {node.__class__.__name__} requires artifact '{inp}'"
                            )
                    # use executor for consistency
                    if nr_repo is not None:
                        last_node_run = nr_repo.create(pr.id, node.__class__.__name__)
                        nr_repo.update_status(last_node_run.id, "RUNNING")
                    # direct call since we only have node instance
                    node_executor.execute(node, context, pipeline_run_id=pr.id if pr_repo is not None else None)
                    if nr_repo is not None and last_node_run is not None:
                        nr_repo.update_status(last_node_run.id, "SUCCESS", finished_at=datetime.datetime.now(datetime.UTC))
                if pr_repo is not None:
                    pr_repo.update_status(pr.id, "SUCCESS", finished_at=datetime.datetime.now(datetime.UTC))
                return
            except Exception:
                if nr_repo is not None and last_node_run is not None:
                    nr_repo.update_status(last_node_run.id, "FAILED", finished_at=datetime.datetime.now(datetime.UTC))
                if pr_repo is not None:
                    pr_repo.update_status(pr.id, "FAILED", finished_at=datetime.datetime.now(datetime.UTC))
                raise

        # build dependency map from attached definitions
        deps = {}
        for node in self.nodes:
            nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None
            if nid is not None:
                deps[nid] = list(getattr(node.definition, 'depends_on', []))

        in_progress = {}
        completed = set()
        lock = threading.Lock()

        # use NodeExecutor for actual execution logic
        from ai_helper.core.executor import NodeExecutor
        node_executor = NodeExecutor(artifact_repo, db_session=db_session)

        def _execute(node: Node):
            nonlocal pr_repo, nr_repo, pr
            nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else node.__class__.__name__
            # delegate to executor (it handles retries, GPU, metrics, logging etc.)
            outputs = node_executor.execute(node, context, pipeline_run_id=pr.id if pr_repo is not None else None)
            with lock:
                completed.add(nid)
            return outputs

        # executor for parallel tasks
        executor = ThreadPoolExecutor()
        futures = {}

        try:
            while len(completed) < len(self.nodes):
                # schedule all ready nodes
                for node in self.nodes:
                    nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None
                    if nid in completed or nid in in_progress:
                        continue
                    deps_ok = all(d in completed for d in deps.get(nid, []))
                    if not deps_ok:
                        continue
                    # check cache
                    key = self._compute_cache_key(node, context)
                    if key in self.cache:
                        # restore outputs
                        for name, aid in self.cache[key].items():
                            context.set_artifact(name, aid)
                        completed.add(nid)
                        continue
                    # schedule execution
                    fut = executor.submit(_execute, node)
                    futures[fut] = node
                    in_progress[nid] = fut
                if not futures and len(completed) < len(self.nodes):
                    # deadlock? possible cycle not detected earlier
                    raise RuntimeError("No runnable nodes found - possible cycle")
                # wait for at least one future to complete before continuing loop
                if futures:
                    from concurrent.futures import wait, FIRST_COMPLETED

                    done_set, _ = wait(futures.keys(), return_when=FIRST_COMPLETED)
                    for fut in done_set:
                        node = futures.pop(fut)
                        nid = getattr(node, 'definition', None).node_id if hasattr(node, 'definition') else None
                        in_progress.pop(nid, None)
                        outputs = fut.result()
                        # record in cache
                        key = self._compute_cache_key(node, context)
                        self.cache[key] = outputs
        except Exception:
            # mark failure on last node run if exists
            if nr_repo is not None and 'last_run' in locals() and last_run is not None:
                nr_repo.update_status(last_run.id, "FAILED", finished_at=datetime.datetime.now(datetime.UTC))
            if pr_repo is not None:
                pr_repo.update_status(pr.id, "FAILED", finished_at=datetime.datetime.now(datetime.UTC))
            raise
        finally:
            executor.shutdown(wait=False)
        # success