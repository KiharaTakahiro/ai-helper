from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository


class VideoInputNode(BaseNode):
    """動画ファイルパスを取り込み、アーティファクト化するサンプルノード。

    Attributes:
        outputs (list[str]): "video" を出力として持つ。
        video_path (str): コンストラクタで渡される入力パス。
    """

    outputs = ["video"]

    def __init__(self, video_path: str):
        """初期化。

        Args:
            video_path (str): 取り込み対象の動画ファイルパス。
        """
        self.video_path = video_path

    def execute(self, context: Context, artifact_repo: ArtifactRepository):
        """実行時処理。

        ファイルパス文字列をアーティファクトとして保存し、
        コンテキストに登録する。
        """
        artifact_id = artifact_repo.save(self.video_path)
        context.set_artifact("video", artifact_id)
