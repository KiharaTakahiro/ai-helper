from fastapi import FastAPI

from ai_helper.core.context import Context
from ai_helper.core.pipeline import Pipeline
from ai_helper.core.registry import NodeFactory
from ai_helper.pipeline.repository import PipelineRepository
from ai_helper.infra.storage.local_repository import LocalArtifactRepository

# DB ヘルパーとリポジトリ
import ai_helper.db.session as dbsess
from ai_helper.repository.artifact_metadata import ArtifactMetadataRepository

# アプリ起動時にノードを登録
from ai_helper.core.registry import register_node
from ai_helper.nodes.video.video_input_node import VideoInputNode
from ai_helper.nodes.video.frame_extract_node import FrameExtractNode


register_node("video_input", VideoInputNode)
register_node("frame_extract", FrameExtractNode)


app = FastAPI()

# シングルトン風にリポジトリとファクトリを保持
repo = PipelineRepository()
node_factory = NodeFactory()

# artifact_repo はリクエストごとに作り直すためここでは生成しない


@app.post("/pipeline/run/{pipeline_id}")
def run_pipeline(pipeline_id: str):
    """指定したIDのパイプラインを取得して実行するエンドポイント"""

    # DB セッションを用意
    session = dbsess.get_session()
    metadata_repo = ArtifactMetadataRepository(session)
    artifact_repo = LocalArtifactRepository(metadata_repo=metadata_repo)

    definition = repo.get_pipeline(pipeline_id)
    # create pipeline object directly from definition (handles DAG, ordering)
    pipeline = Pipeline.from_definition(definition, node_factory=node_factory)
    # パイプラインIDを pipeline.run が知るよう属性は from_definition が設定
    context = Context()
    pipeline.run(context, artifact_repo, db_session=session)
    return {
        "artifacts": context.artifacts
    }
