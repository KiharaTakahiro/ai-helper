"""サンプルの FaceSwap パイプライン定義。

動画ファイルを入力とし、フレーム抽出 → 顔差し替え → エンコードという
簡単なワークフローを構築する。CLI や他のスクリプトから直接インポートして
利用できるように、実行可能な ``pipeline`` オブジェクトをエクスポートする。
"""

from ai_helper.pipeline.models import PipelineDefinition, NodeDefinition
from ai_helper.core.pipeline import Pipeline
from ai_helper.core.registry import register_node

# 内部ノードをインポートすることでモジュール読み込み時にクラスが登録される
from ai_helper.nodes.video.video_input_node import VideoInputNode
from ai_helper.nodes.video.frame_extract_node import FrameExtractNode
from ai_helper.nodes.video.encode_video_node import EncodeVideoNode

# プラグインノードは import で自動登録される
import ai_helper.plugins.faceswap_plugin

# フレンドリーな名前で登録し直す（自動スキャン時の名称は不定）
register_node("video_input", VideoInputNode)
register_node("frame_extract", FrameExtractNode)
register_node("encode_video", EncodeVideoNode)
# faceswap はプラグイン側で "faceswap" として登録済み

# パイプライン定義
definition = PipelineDefinition(
    id="faceswap_demo",
    nodes=[
        NodeDefinition(node_id="video", node_type="video_input", config={"video_path": "sample.mp4"}, depends_on=[]),
        NodeDefinition(node_id="frames", node_type="frame_extract", config={}, depends_on=["video"]),
        NodeDefinition(node_id="swap", node_type="faceswap", config={}, depends_on=["frames"]),
        NodeDefinition(node_id="encode", node_type="encode_video", config={}, depends_on=["swap"]),
    ],
)

# 実行可能なパイプラインオブジェクト
pipeline = Pipeline.from_definition(definition)
