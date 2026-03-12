from ai_helper.pipeline.models import PipelineDefinition, NodeDefinition


class PipelineRepository:
    """パイプライン定義を取得するリポジトリインターフェース。

    現在はデモ用に `demo` ID に応じたハードコード定義を返すだけ。
    将来的にはデータベースアクセスを実装する予定。
    """

    def get_pipeline(self, pipeline_id: str) -> PipelineDefinition:
        """指定IDのパイプライン定義を返す。

        Args:
            pipeline_id (str): パイプライン識別子。

        Returns:
            PipelineDefinition: 定義オブジェクト。

        Raises:
            ValueError: 指定IDが存在しない場合。
        """

        if pipeline_id == "demo":
            # example DAG: video_input -> frame_extract
            return PipelineDefinition(
                id="demo",
                nodes=[
                    NodeDefinition(
                        node_id="video",
                        node_type="video_input",
                        config={"video_path": "sample.mp4"},
                        depends_on=[],
                    ),
                    NodeDefinition(
                        node_id="frames",
                        node_type="frame_extract",
                        config={},
                        depends_on=["video"],
                    ),
                ],
            )

        raise ValueError("Pipeline not found")
