# AI Helper

軽量な AI ワークフローエンジン。ソース内コメントは日本語で記述し、
スタイルは `CODE_STYLE.md` に従います。

⚠️ 依存関係の追加・更新は **必ず Poetry** (`pyproject.toml`) を使って行ってください。`pip install` を直接使用しないでください。

## ディレクトリ構成
```
ai_helper/
    core/          # 基本クラス
    artifact/      # アーティファクトリポジトリ
    node/          # ノード登録・生成
    pipeline/      # パイプライン関連モデル
    db/            # (将来用) DB 層
    nodes/         # サンプルノード
    api/           # FastAPI アプリ
    config/        # 設定
```

## 使用例
```python
from ai_helper.core.context import Context
from ai_helper.artifact.local_repository import LocalArtifactRepository
from ai_helper.node.registry import register_node
# ノードを定義・登録してパイプラインを組み立てる
```

## API
サーバ起動:
```
uvicorn ai_helper.api.main:app --reload
```

パイプライン実行:
```
POST /pipeline/run/demo
```

このエンドポイントを叩くと内部でデフォルトSQLite DBに実行履歴が記録されます:

* `pipeline_run` テーブル - パイプライン全体の状態
* `node_run` テーブル     - 各ノードの開始/終了ステータス
* `artifact` テーブル     - 保存したアーティファクトのメタデータ

ログ機能は将来 GUI バリデーションや監視に活用できます。

詳細は `design.md` を参照してください。

コーディング規約は `CODE_STYLE.md` にまとめています。
