from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()


class PipelineRun(Base):
    """Pipeline実行履歴を保存するテーブル。

    ```
    1回のPipeline.run()ごとに1レコード作成される。
    ```
    """

    __tablename__ = "pipeline_run"

    id = Column(String, primary_key=True)
    pipeline_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    finished_at = Column(DateTime, nullable=True)

    node_runs = relationship("NodeRun", back_populates="pipeline_run")


class NodeRun(Base):
    """個々のノード実行ログを保存するテーブル。"""

    __tablename__ = "node_run"

    id = Column(String, primary_key=True)
    pipeline_run_id = Column(String, ForeignKey("pipeline_run.id"), nullable=False)
    node_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    finished_at = Column(DateTime, nullable=True)
    # new metrics
    execution_time = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)

    pipeline_run = relationship("PipelineRun", back_populates="node_runs")


class Artifact(Base):
    """アーティファクトメタデータを保存するテーブル。"""

    __tablename__ = "artifact"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    repository_path = Column(String, nullable=False)


class Pipeline(Base):
    """パイプライン定義の識別を保持するテーブル。"""

    __tablename__ = "pipeline"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class PipelineVersion(Base):
    """各パイプラインのバージョン履歴を保存するテーブル。"""

    __tablename__ = "pipeline_version"

    id = Column(String, primary_key=True)
    pipeline_id = Column(String, ForeignKey("pipeline.id"), nullable=False)
    version = Column(String, nullable=False)
    definition = Column(String, nullable=False)  # JSON serialized
