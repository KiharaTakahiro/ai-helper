from ai_helper.db.session import create_sqlite_session
from ai_helper.core.pipeline import Pipeline
from ai_helper.artifact.local_repository import LocalArtifactRepository
from ai_helper.pipeline.repository import PipelineRepository
from ai_helper.node.factory import NodeFactory
from ai_helper.core.context import Context
from ai_helper.node.registry import register_node
from ai_helper.nodes.video_input_node import VideoInputNode
from ai_helper.nodes.frame_extract_node import FrameExtractNode

# register nodes as API does
def register_demo_nodes():
    register_node("video_input", VideoInputNode)
    register_node("frame_extract", FrameExtractNode)


if __name__ == "__main__":
    session = create_sqlite_session()
    print("session", session)

    repo = PipelineRepository()
    definition = repo.get_pipeline("demo")
    print("definition", definition)

    register_demo_nodes()
    # build pipeline using new helper (handles DAG/depends_on)
    pipeline = Pipeline.from_definition(definition)
    pipeline.definition = definition

    artifact_repo = LocalArtifactRepository()
    context = Context()
    pipeline.run(context, artifact_repo, db_session=session)

    from ai_helper.db.models import PipelineRun, NodeRun, Artifact

    print("counts", session.query(PipelineRun).count(), session.query(NodeRun).count(), session.query(Artifact).count())
