from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository


class FaceDetectNode(BaseNode):
    """フレームリストから顔検出情報を生成するダミーノード。

    実際の顔検出処理は後で実装する。
    """

    name = "face_detect"
    tags = ["video", "detect"]

    inputs = ["frames"]
    outputs = ["faces"]

    def execute(self, context: Context, artifact_repo: ArtifactRepository):
        try:
            aid = context.get_artifact("frames")
            frames = artifact_repo.load(aid)
        except KeyError:
            frames = []
        # ダミーとして空リストを返す
        faces = []
        new_id = artifact_repo.save(faces)
        context.set_artifact("faces", new_id)
