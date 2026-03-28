# debug_pipeline.py

from ai_helper.core.pipeline import Pipeline
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository

from ai_helper.nodes.video_input_node import VideoInputNode


def create_node(node_id, depends_on=None):
    node = VideoInputNode(video_path="test.mp4")

    # definitionを付ける
    node.definition = type("Def", (), {})()
    node.definition.node_id = node_id
    node.definition.depends_on = depends_on or []

    return node


def main():
    node1 = create_node("step1")

    pipeline = Pipeline(nodes=[node1])

    context = Context()
    repo = ArtifactRepository()

    pipeline.run(context, repo)


if __name__ == "__main__":
    main()