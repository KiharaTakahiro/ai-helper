import datetime
import uuid
from sqlalchemy.orm import Session
from ai_helper.db.models import NodeRun


class NodeRunRepository:
    """NodeRun テーブルへの操作を提供するリポジトリ"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, pipeline_run_id: str, node_type: str) -> NodeRun:
        run = NodeRun(
            id=str(uuid.uuid4()),
            pipeline_run_id=pipeline_run_id,
            node_type=node_type,
            status="PENDING",
            started_at=datetime.datetime.now(datetime.UTC),
        )
        self.session.add(run)
        self.session.commit()
        return run

    def update_status(
        self,
        run_id: str,
        status: str,
        finished_at: datetime.datetime | None = None,
        execution_time: float | None = None,
        memory_usage: float | None = None,
    ):
        """NodeRun レコードのステータスおよびメトリクスを更新する。

        Args:
            run_id (str): 更新対象の NodeRun レコード ID。
            status (str): 新しいステータス文字列。
            finished_at (datetime | None): 実行終了時刻。未指定の場合は変更しない。
            execution_time (float | None): 実行時間（秒）。
            memory_usage (float | None): メモリ使用量（MB など）。

        Returns:
            NodeRun: 更新後のオブジェクト。

        Raises:
            ValueError: run_id に該当するレコードが存在しない場合。
        """
        run = self.session.get(NodeRun, run_id)
        if run is None:
            raise ValueError(f"NodeRun {run_id} not found")
        run.status = status
        if finished_at is not None:
            run.finished_at = finished_at
        if execution_time is not None:
            run.execution_time = execution_time
        if memory_usage is not None:
            run.memory_usage = memory_usage
        self.session.commit()
        return run
