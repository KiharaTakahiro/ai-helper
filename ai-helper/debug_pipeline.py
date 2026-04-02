# debug_pipeline.py

from ai_helper.core.pipeline import Pipeline
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository
from ai_helper.core.log.logging_config import setup_logging
from ai_helper.nodes.video_input_node import VideoInputNode
import logging



def main():
    setup_logging(log_level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("[開始] デバッグ用パイプライン実行")
    pipeline = Pipeline.from_dict({
        "nodes": [
            {
                "node_id": "step1",
                "node_type": "video_input",
                "config": {"video_path": "test.mp4"},
                "depends_on": [],
            }
        ]
    })

    context = Context()
    repo = ArtifactRepository()
    logger.info("[開始] パイプライン実行")
    pipeline.run(context, repo)
    logger.info("[完了] パイプライン実行")
    logger.info("[完了] デバッグ用パイプライン実行")


if __name__ == "__main__":
    main()