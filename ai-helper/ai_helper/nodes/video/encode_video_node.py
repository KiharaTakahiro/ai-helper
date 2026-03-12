from ai_helper.core.node import Node
from ai_helper.core.context import Context
from ai_helper.core.artifact.repository import ArtifactRepository
from ai_helper.core.registry import register_node


class EncodeVideoNode(Node):
    """動画またはフレームリストを受け取りエンコード済みデータを出力するノード。

    本実装では実際のエンコード処理は行わず、
    入力オブジェクトに "encoded_" という接頭辞を付加した文字列を保存するだけの
    ダミー実装となっている。

    Attributes:
        inputs (list[str]): 必要とする入力アーティファクト名（"swapped"）。
        outputs (list[str]): 出力するアーティファクト名（"encoded"）。
        config (dict): コンストラクタ引数として渡される設定オブジェクト。
    """

    inputs = ["swapped"]
    outputs = ["encoded"]

    def __init__(self, **config):
        """初期化。

        Args:
            config (dict): ノード固有の設定。
        """
        self.config = config

    def run(self, context: Context, artifact_repo: ArtifactRepository):
        """ノード実行時のエントリポイント。

        Args:
            context (Context): パイプライン実行コンテキスト。
            artifact_repo (ArtifactRepository): アーティファクトの保存/読み込み用リポジトリ。
        """
        # 入力アーティファクトの取得
        aid = context.get_artifact("swapped")
        frames = artifact_repo.load(aid)

        # ダミーのエンコード処理
        encoded = f"encoded_{frames}"

        new_id = artifact_repo.save(encoded)
        context.set_artifact("encoded", new_id)


# フレンドリーネームで登録
register_node("encode_video", EncodeVideoNode)
