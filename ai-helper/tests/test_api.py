# tests/test_api.py
# API 層の挙動を確認する。視点:
#  - エンドポイント呼び出し時にパイプラインが実行されること
#  - 内部で提供される DB セッションがパッチされる際にログが残ること
# これにより `ai_helper.api.main` の処理と依存モジュールが網羅される。

from fastapi.testclient import TestClient

import ai_helper.db.session as dbsess
from ai_helper.db.models import PipelineRun, NodeRun, Artifact
from ai_helper.db.session import create_sqlite_session
from ai_helper.api.main import app


def test_api_endpoint_records(tmp_path):
    # 観点: エンドポイント呼び出し時にパイプラインが実行されること。
    #       セッションをパッチしてDBへのレコード化を観察する。
    # prepare a shared in-memory DB session and patch get_session
    session = create_sqlite_session()
    # patch both the db session module and the api.main reference just in case
    dbsess.get_session = lambda: session
    import ai_helper.api.main as api_main
    api_main.dbsess.get_session = lambda: session

    client = TestClient(app)
    response = client.post("/pipeline/run/demo")
    assert response.status_code == 200
    # check that pipeline_run and node_run and artifact entries exist
    assert session.query(PipelineRun).count() == 1
    assert session.query(NodeRun).count() == 2  # demo pipeline has two nodes
    assert session.query(Artifact).count() >= 1
    # verify response contains artifacts keys
    assert "artifacts" in response.json()
