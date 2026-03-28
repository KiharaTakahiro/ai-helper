# debug_pipeline.py

from ai_helper.core.pipeline import Pipeline
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository
from ai_helper.core.log.logging_config import setup_logging
from ai_helper.nodes.video_input_node import VideoInputNode
import logging

def create_node(node_id, depends_on=None):
    node = VideoInputNode(video_path="test.mp4")

    # definitionを付ける
    node.definition = type("Def", (), {})()
    node.definition.node_id = node_id
    node.definition.depends_on = depends_on or []

    return node


def main():
    setup_logging(log_level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("[開始] デバッグ用パイプライン実行")
    logger.info("[開始] ノード作成")
    node1 = create_node("step1")
    logger.info("[完了] ノード作成")
    pipeline = Pipeline(nodes=[node1])

    context = Context()
    repo = ArtifactRepository()
    logger.info("[開始] パイプライン実行")
    pipeline.run(context, repo)
    logger.info("[完了] パイプライン実行")
    logger.info("[完了] デバッグ用パイプライン実行")


if __name__ == "__main__":
    main()