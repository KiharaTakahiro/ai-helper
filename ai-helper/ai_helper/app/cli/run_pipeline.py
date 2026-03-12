"""コマンドラインからパイプライン定義を読み込み実行するユーティリティ。

Python モジュールまたは YAML ファイルで定義されたパイプラインを受け取り、
実行結果を標準出力に表示する。コンテキスト内のアーティファクト内容も
簡易的にダンプされる。
"""

import argparse
import importlib.util
import sys
import os

from ai_helper.core.pipeline import Pipeline
from ai_helper.core.context import Context
from ai_helper.infra.storage.local_repository import LocalArtifactRepository
from ai_helper.pipeline.models import PipelineDefinition


def load_pipeline(path: str) -> Pipeline:
    """指定パスからパイプラインを読み込んで ``Pipeline`` インスタンスを返す。

    Args:
        path (str): Python モジュール (.py) または YAML (.yaml/.yml) のパス。
    Raises:
        ValueError: 読み込み失敗や形式不正の場合。
    """
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("_pipeline_module", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)  # type: ignore

        # いくつかの候補名を探す
        if hasattr(module, "pipeline"):
            return module.pipeline
        if hasattr(module, "definition"):
            return Pipeline.from_definition(module.definition)
        if hasattr(module, "create_pipeline"):
            obj = module.create_pipeline()
            if isinstance(obj, Pipeline):
                return obj
            return Pipeline.from_definition(obj)
        raise ValueError("no pipeline object found in module")

    if path.endswith(('.yml', '.yaml')):
        try:
            import yaml
        except ImportError:
            raise ValueError("YAML support requires PyYAML; please install it")
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        # assume dict convertible to PipelineDefinition
        pd = PipelineDefinition(**data)
        return Pipeline.from_definition(pd)

    raise ValueError(f"unsupported pipeline file type: {path}")


def main():
    parser = argparse.ArgumentParser(description="Run an AI helper pipeline")
    parser.add_argument("pipeline", help="path to pipeline definition (py or yaml)")
    args = parser.parse_args()

    path = args.pipeline
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    print(f"Loading pipeline from {path}")
    pipeline = load_pipeline(path)

    repo = LocalArtifactRepository()
    ctx = Context()

    print("starting run...")
    pipeline.run(ctx, repo)
    print("Pipeline finished")

    print("Artifacts in context:")
    for name, aid in ctx.artifacts.items():
        try:
            val = repo.load(aid)
        except Exception as e:
            val = f"<error loading artifact: {e}>"
        print(f" - {name}: {aid} -> {val}")


if __name__ == "__main__":
    main()
