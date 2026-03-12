# SQLAlchemy セッション管理のヘルパー関数群。
# このモジュール内のコメント・docstring は日本語で記述する方針。

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


def create_sqlite_session(db_url: str = "sqlite:///:memory:"):
    """指定されたデータベース URL で新しい SQLAlchemy セッションを返す。

    デフォルトではメモリ内 SQLite を使用し、`Base` に定義されたすべての
    テーブルが作成される。複数のセッションを同じインメモリ DB で共有
    するために特殊なエンジン設定を行っている。

    Args:
        db_url (str): 接続先データベースの URL。

    Returns:
        Session: 新しく構築されたセッションオブジェクト。
    """
    # メモリ内 SQLite では接続ごとに新しい空の DB が生成されてしまうため、
    # 静的プールとチェックの無効化で接続を再利用する。
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        db_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def get_session():
    """デフォルトのメモリ内 SQLite セッションを簡単に取得するためのアクセサ。

    内部では create_sqlite_session() を呼び出すだけで、特に引数は不要である。
    """
    return create_sqlite_session()
