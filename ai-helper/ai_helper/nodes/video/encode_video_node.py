from ai_helper.core.node.base_node import BaseNode
from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository
from ai_helper.core.registry import register_node


class EncodeVideoNode(BaseNode):
    """動画またはフレームリストを受け取りエンコード済みデータを出力するノード。

    Attributes:
        name (str): ノード登録名。
        tags (list[str]): ノードに関連付けるタグ。
    """

    name = "encode_video"
    tags = ["video", "encode"]

    # 実装注釈:
    # 本実装では実際のエンコード処理は行わず、
    # 入力オブジェクトに "encoded_" という接頭辞を付加した文字列を保存する
    # だけのダミー実装となっている。
    # 以下は前のドキュメントで記載していた属性説明を継続。
    inputs = ["swapped"]
    outputs = ["encoded"]

    inputs = ["swapped"]
    outputs = ["encoded"]

    def __init__(self, **config):
        """初期化。

        Args:
            config (dict): ノード固有の設定。
        """
        self.config = config

    def execute(self, context: Context, artifact_repo: ArtifactRepository):
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
