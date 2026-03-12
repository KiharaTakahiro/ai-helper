# ダミー実装（AI処理なし）

from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.artifact.repository import ArtifactRepository


class FrameExtractNode(Node):
    """動画ファイルからフレームを抽出してアーティファクト化するサンプルノード。

    実際には動画解析を行わず、渡されたパス文字列に
    "_frame_1" と "_frame_2" を付加した擬似フレームリストを返す。
    
    Attributes:
        inputs (list[str]): 必要とするアーティファクト名のリスト（"video"）。
        outputs (list[str]): 出力するアーティファクト名のリスト（"frames"）。
    """

    inputs = ["video"]
    outputs = ["frames"]

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        """ノード実行時に呼ばれるエントリポイント。

        Args:
            context (Context): パイプライン実行時の共有コンテキスト。
            artifact_repo (ArtifactRepository): アーティファクト保存/読み込み用リポジトリ。

        Raises:
            KeyError: 必要な入力アーティファクトがコンテキストに存在しない場合。

        処理:
            1. コンテキストから "video" アーティファクトIDを取得
            2. リポジトリからパス文字列を読み込み
            3. 擬似フレームリストを生成
            4. フレームリストをリポジトリに保存し "frames" としてコンテキストに登録
        """
        # 動画アーティファクトIDを取得
        video_artifact = context.get_artifact("video")

        # リポジトリから元データ（パス文字列）を読み込む
        video_path = artifact_repo.load(video_artifact)

        # 擬似的に2フレーム分を生成
        frames = [
            f"{video_path}_frame_1",
            f"{video_path}_frame_2",
        ]

        artifact_id = artifact_repo.save(frames)
        context.set_artifact("frames", artifact_id)
