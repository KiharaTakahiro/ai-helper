from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository


class VideoInputNode(Node):
    """動画ファイルパスを取り込み、アーティファクト化するサンプルノード。

    Attributes:
        name (str): ノード登録名。
        tags (list[str]): ノードに関連付けるタグ一覧。
        outputs (list[str]): "video" を出力として持つ。
        video_path (str): コンストラクタで渡される入力パス。
    """

    name = "video_input"
    tags = ["video", "input"]

    outputs = ["video"]

    def __init__(self, video_path: str):
        """初期化。

        Args:
            video_path (str): 取り込み対象の動画ファイルパス。
        """
        self.video_path = video_path

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        """実行時処理。

        ファイルパス文字列をアーティファクトとして保存し、
        コンテキストに登録する。
        """
        artifact_id = artifact_repo.save(self.video_path)
        context.set_artifact("video", artifact_id)
