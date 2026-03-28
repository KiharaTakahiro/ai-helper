"""
API エントリーポイント。

このモジュールは ai-helper の HTTP API を起動する。

主な責務

- Web アプリケーションの生成
- API Router の登録
- HTTP サーバ起動

設計方針

API 層にはビジネスロジックを記述しない。
実際の処理は core 層のサービスへ委譲する。
"""

import logging
from fastapi import FastAPI

from ai_helper.core.context import Context
from ai_helper.core.pipeline import Pipeline
from ai_helper.core.registry import NodeFactory
from ai_helper.pipeline.repository import PipelineRepository
from ai_helper.infra.storage.local_repository import LocalArtifactRepository
from ai_helper.core.log.logging_config import setup_logging

# DB ヘルパーとリポジトリ
import ai_helper.infra.db.session as dbsess
from ai_helper.repository.artifact_metadata import ArtifactMetadataRepository

# アプリ起動時にノードを登録
from ai_helper.core.registry import register_node
from ai_helper.nodes.video.video_input_node import VideoInputNode
from ai_helper.nodes.video.frame_extract_node import FrameExtractNode


register_node("video_input", VideoInputNode)
register_node("frame_extract", FrameExtractNode)

# FastAPI アプリケーションインスタンス
# このアプリが HTTP API のエントリーポイントになる
app = FastAPI()

# シングルトン風にリポジトリとファクトリを保持
repo = PipelineRepository()
node_factory = NodeFactory()

# artifact_repo はリクエストごとに作り直すためここでは生成しない
setup_logging(log_level=logging.DEBUG)
logger = logging.getLogger(__name__)


@app.post("/pipeline/run/{pipeline_id}")
def run_pipeline(pipeline_id: str):
    """指定したIDのパイプラインを取得して実行するエンドポイント"""
    logger.info(f"[開始] パイプライン実行リクエスト (pipeline_id={pipeline_id})")
    # DB セッションを用意
    session = dbsess.get_session()
    metadata_repo = ArtifactMetadataRepository(session)
    artifact_repo = LocalArtifactRepository(metadata_repo=metadata_repo)

    definition = repo.get_pipeline(pipeline_id)
    # 定義から直接Pipelineオブジェクトを生成する（DAG構造と実行順序を処理する）
    pipeline = Pipeline.from_definition(definition, node_factory=node_factory)
    # パイプラインIDを pipeline.run が知るよう属性は from_definition が設定
    context = Context()
    pipeline.run(context, artifact_repo, db_session=session)
    logger.info(f"[完了] パイプライン実行完了 (pipeline_id={pipeline_id})")
    return {
        "artifacts": context.artifacts
    }
