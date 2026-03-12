import datetime
import uuid
from sqlalchemy.orm import Session
from ai_helper.infra.db.models import PipelineRun


class PipelineRunRepository:
    """PipelineRun テーブルへのアクセスを提供するリポジトリ"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, pipeline_id: str) -> PipelineRun:
        """新しい PipelineRun レコードを生成して返す"""
        run = PipelineRun(
            id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            status="PENDING",
            created_at=datetime.datetime.now(datetime.UTC),
        )
        self.session.add(run)
        self.session.commit()
        return run

    def update_status(self, run_id: str, status: str, finished_at: datetime.datetime | None = None):
        """指定ランのステータスを更新する"""
        run = self.session.get(PipelineRun, run_id)
        if run is None:
            raise ValueError(f"PipelineRun {run_id} not found")
        run.status = status
        if finished_at is not None:
            run.finished_at = finished_at
        self.session.commit()
        return run
