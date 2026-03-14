# tests/test_api.py
# API 層の挙動を確認する。視点:
#  - エンドポイント呼び出し時にパイプラインが実行されること
#  - 内部で提供される DB セッションがパッチされる際にログが残ること
# これにより `ai_helper.api.main` の処理と依存モジュールが網羅される。

from fastapi.testclient import TestClient

import ai_helper.infra.db.session as dbsess
from ai_helper.infra.db.models import PipelineRun, NodeRun, Artifact
from ai_helper.infra.db.session import create_sqlite_session
from ai_helper.api.main import app


def test_api_endpoint_records(tmp_path):
    # 観点: エンドポイント呼び出し時にパイプラインが実行されること。
    #       セッションをパッチしてDBへのレコード化を観察する。
    # 共通のインメモリDBセッションを用意し、get_session をパッチする
    session = create_sqlite_session()
    # 念のため db session モジュールと api.main の参照先双方をパッチ
    dbsess.get_session = lambda: session
    import ai_helper.api.main as api_main
    api_main.dbsess.get_session = lambda: session

    client = TestClient(app)
    response = client.post("/pipeline/run/demo")
    assert response.status_code == 200
    # pipeline_run, node_run, artifact のレコードが作成されていることを確認
    assert session.query(PipelineRun).count() == 1
    assert session.query(NodeRun).count() == 2  # demo パイプラインは2つのノードを持つ
    assert session.query(Artifact).count() >= 1
    # レスポンスに artifacts キーが含まれることを検証
    assert "artifacts" in response.json()
