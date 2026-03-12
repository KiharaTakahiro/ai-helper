import uuid
from sqlalchemy.orm import Session
from ai_helper.db.models import Pipeline, PipelineVersion
import json


class PipelineRepository:
    """パイプライン定義を取得・登録するリポジトリ。"""

    def __init__(self, session: Session):
        self.session = session

    def create_pipeline(self, name: str) -> Pipeline:
        p = Pipeline(id=str(uuid.uuid4()), name=name)
        self.session.add(p)
        self.session.commit()
        return p

    def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        return self.session.get(Pipeline, pipeline_id)


class PipelineVersionRepository:
    """パイプラインバージョンの作成・取得を行うリポジトリ。"""

    def __init__(self, session: Session):
        self.session = session

    def create_version(self, pipeline_id: str, version: str, definition: dict) -> PipelineVersion:
        pv = PipelineVersion(
            id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            version=version,
            definition=json.dumps(definition, sort_keys=True),
        )
        self.session.add(pv)
        self.session.commit()
        return pv

    def get_latest(self, pipeline_id: str) -> PipelineVersion | None:
        return (
            self.session.query(PipelineVersion)
            .filter(PipelineVersion.pipeline_id == pipeline_id)
            .order_by(PipelineVersion.version.desc())
            .first()
        )
