"""
パイプラインをCLIから実行するためのエントリーポイント。

このモジュールはコマンドラインからパイプライン定義を読み込み、
Pipeline を生成して実行するためのユーティリティを提供する。

対応するパイプライン定義形式

- Python module (.py)
- YAML (.yaml / .yml)

CLI層の責務は以下に限定する。

1. CLI引数の取得
2. Pipeline定義の読み込み
3. Pipelineオブジェクト生成
4. Pipelineの実行

実際の処理ロジックは core 層 (Pipeline / Node) に委譲される。
CLI層はビジネスロジックを持たない。
"""

import argparse
import importlib.util
import sys
import os

from ai_helper.core.pipeline import Pipeline
from ai_helper.core.context import Context
from ai_helper.infra.storage.local_repository import LocalArtifactRepository
from ai_helper.pipeline.models import PipelineDefinition

# -------------------------------------------------------------
# Pipeline Loader
#
# CLIから指定されたパイプライン定義を読み込み Pipeline を生成する。
#
# ai-helper では Pipeline 定義方法を複数サポートしている。
#
# 1 Python module
#   - pipeline 変数
#   - definition (PipelineDefinition)
#   - create_pipeline()
#
# 2 YAML
#   - declarative pipeline definition
#
# この柔軟性により
#
# ・簡単なpipeline → YAML
# ・複雑なpipeline → Python
#
# の使い分けが可能になる。
# -------------------------------------------------------------
def load_pipeline(path: str) -> Pipeline:
    """指定パスからパイプラインを読み込み ``Pipeline`` を生成する。

    パイプライン定義は複数の形式をサポートする。

    - Python module
    - YAML

    Python module の場合は以下のパターンを探索する。

    - ``pipeline`` : 既に生成済みの Pipeline
    - ``definition`` : PipelineDefinition
    - ``create_pipeline()`` : Pipeline生成関数

    これにより、ユーザーは用途に応じて
    declarative / imperative の両方のスタイルで
    パイプラインを定義できる。

    Args:
        path: パイプライン定義ファイル

    Returns:
        Pipeline

    Raises:
        ValueError: 読み込み失敗や形式不正
    """
    # Pythonモジュールとしてパイプラインをロードする
    # ユーザー定義Pipelineを動的に読み込むため importlib を使用する
    if path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("_pipeline_module", path)
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # モジュール内からPipeline定義を探索する
        # 複数の書き方を許可することでユーザーの自由度を確保する
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

    # YAML形式のパイプライン定義を読み込む
    # declarativeにPipelineを記述できるようにするための形式
    if path.endswith(('.yml', '.yaml')):
        return Pipeline.from_yml(path)

    raise ValueError(f"unsupported pipeline file type: {path}")


def main():
    """CLIエントリーポイント。

    CLI引数で指定されたパイプライン定義を読み込み、
    Pipelineを実行する。

    実行後は Context に格納された Artifact を簡易表示する。
    """
    parser = argparse.ArgumentParser(description="Run an AI helper pipeline")
    parser.add_argument("pipeline", help="path to pipeline definition (py or yaml)")
    args = parser.parse_args()

    path = args.pipeline
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    print(f"Loading pipeline from {path}")
    pipeline = load_pipeline(path)

    # Artifact保存先としてローカルRepositoryを使用する
    # CLI用途のデフォルト実装
    repo = LocalArtifactRepository()
    
    # Pipeline実行コンテキスト
    ctx = Context()

    print("starting run...")
    # Pipeline 実行
    #
    # Pipeline.run は以下の処理を内部で行う
    #
    # 1 Node依存関係(DAG)解決
    # 2 実行順序決定
    # 3 Node実行
    # 4 Artifact保存
    #
    # CLIは実行結果の表示のみ担当する
    pipeline.run(ctx, repo)
    print("Pipeline finished")

    # 実行結果として Context に格納された Artifact を表示する
    # CLI利用時のデバッグ用途
    print("Artifacts in context:")
    for name, aid in ctx.artifacts.items():
        try:
            val = repo.load(aid)
        except Exception as e:
            val = f"<error loading artifact: {e}>"
        print(f" - {name}: {aid} -> {val}")


if __name__ == "__main__":
    main()
