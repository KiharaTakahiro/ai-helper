"""Core executor package containing NodeExecutor."""

from typing import Dict, List
import datetime
import time
import tracemalloc

from ai_helper.core.context import Context
from ai_helper.core.node import Node
from ai_helper.core.repository.artifact_repository import ArtifactRepository


class NodeExecutor:
    """
    ノード定義またはインスタンスを実行するためのユーティリティクラス。

    パイプライン全体を扱う ``Pipeline`` とは独立しており、
    単体ノードのデバッグ実行や再利用に便利である。

    Attributes:
        artifact_repo (ArtifactRepository): アーティファクト永続化用リポジトリ。
        db_session: 任意のデータベースセッション（SQLAlchemyなど）。
        nr_repo: NodeRunRepository（セッションが与えられた場合）。
        pr_repo: PipelineRunRepository（同上）。
    """

    def __init__(self, artifact_repo: ArtifactRepository, db_session=None):
        self.artifact_repo = artifact_repo
        self.db_session = db_session
        self.nr_repo = None
        self.pr_repo = None
        if db_session is not None:
            from ai_helper.repository import NodeRunRepository, PipelineRunRepository

            self.nr_repo = NodeRunRepository(db_session)
            self.pr_repo = PipelineRunRepository(db_session)

    def execute(
        self,
        node_or_def,
        context: Context,
        pipeline_run_id: str | None = None,
    ) -> Dict[str, str]:
        """
        ノード定義または ``Node`` インスタンスを与えて実行する。

        Args:
            node_or_def: ``Node`` インスタンスか ``NodeDefinition`` オブジェクト。
            context (Context): 実行コンテキスト。
            pipeline_run_id (str | None): パイプライン実行ID。ログ記録用。

        Returns:
            Dict[str, str]: 出力アーティファクト名 -> アーティファクトID のマップ。
        """
        # instantiate if we got a definition
        if not isinstance(node_or_def, Node):
            # avoid circular import by importing inside
            from ai_helper.core.registry.factory import NodeFactory

            factory = NodeFactory()
            node = factory.create(node_or_def.node_type, node_or_def.config)
            node.definition = node_or_def
        else:
            node = node_or_def

        # begin metrics/logging
        nid = getattr(node, "definition", None).node_id if hasattr(node, "definition") else node.__class__.__name__

        start = time.perf_counter()
        tracemalloc.start()

        last_run = None
        if self.nr_repo is not None and pipeline_run_id is not None:
            last_run = self.nr_repo.create(pipeline_run_id, node.__class__.__name__)
            self.nr_repo.update_status(last_run.id, "RUNNING")

        attempts = 0
        while True:
            try:
                # GPU check
                if getattr(node.definition, "requires_gpu", False) and not _gpu_available():
                    # mark skipped in log and return immediately
                    if self.nr_repo is not None and last_run is not None:
                        self.nr_repo.update_status(
                            last_run.id,
                            "SKIPPED",
                            finished_at=datetime.datetime.now(datetime.UTC),
                        )
                    return {}

                # type validation before
                self._validate_types(node, context)
                node.run(context, self.artifact_repo)
                # type validation after
                self._check_output_types(node, context)
                break
            except Exception:
                attempts += 1
                if attempts > getattr(node.definition, "retry_count", 0):
                    # log failure if applicable
                    if self.nr_repo is not None and last_run is not None:
                        self.nr_repo.update_status(
                            last_run.id,
                            "FAILED",
                            finished_at=datetime.datetime.now(datetime.UTC),
                        )
                    raise
                time.sleep(getattr(node.definition, "retry_delay", 0))

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.perf_counter() - start

        if self.nr_repo is not None and last_run is not None:
            self.nr_repo.update_status(
                last_run.id,
                "SUCCESS",
                finished_at=datetime.datetime.now(datetime.UTC),
                execution_time=elapsed,
                memory_usage=peak,
            )

        # collect outputs
        if isinstance(node.outputs, dict):
            out_names = list(node.outputs.keys())
        else:
            out_names = list(node.outputs)
        return {name: context.artifacts.get(name) for name in out_names}

    def _validate_types(self, node: Node, context: Context):
        """内部で型チェックを行う（Pipeline と同等）。"""
        if isinstance(node.inputs, dict):
            if getattr(self.artifact_repo, "metadata_repo", None) is not None:
                for name, expected in node.inputs.items():
                    aid = context.artifacts.get(name)
                    if aid is None:
                        raise ValueError(f"Node {node.definition.node_id} missing input '{name}'")
                    rec = self.artifact_repo.metadata_repo.get(aid)
                    if rec and rec.type != expected:
                        raise TypeError(
                            f"artifact '{name}' has type {rec.type} but node expects {expected}"
                        )

    def _check_output_types(self, node: Node, context: Context):
        if isinstance(node.outputs, dict):
            if getattr(self.artifact_repo, "metadata_repo", None) is not None:
                for name, expected in node.outputs.items():
                    aid = context.artifacts.get(name)
                    if aid is None:
                        raise ValueError(
                            f"Node {node.definition.node_id} failed to produce output '{name}'"
                        )
                    rec = self.artifact_repo.metadata_repo.get(aid)
                    if rec and rec.type != expected:
                        raise TypeError(
                            f"output artifact '{name}' has type {rec.type} but node declared {expected}"
                        )


# GPU availability helper shared across modules

def _gpu_available():
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False
