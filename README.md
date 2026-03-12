# ai-helper

軽量な **AI ワークフローエンジン** です。  
複数の処理ノードを組み合わせて、AI による複雑な処理をパイプラインとして定義・実行できます。  

---

## 🔍 What is ai-helper?

ai-helper は、以下のような用途を想定した **AI Workflow Engine** です：

- 動画／画像処理パイプライン  
- face swap、voice swap など AI 処理の連携  
- 複数モデル・ツールを組み合わせた自動化処理

各処理ステップは **Node** として構成され、Pipeline として順番に実行されます。  

---

## 🧱 Core Concepts

| 用語 | 説明 |
|------|------|
| **Pipeline** | Node を順番に実行する処理単位 |
| **Node** | 個別処理（入力 → 処理 → 出力） |
| **Context** | 実行中に Node 間で共有される状態 |
| **Artifact** | Node の出力データを表すメタデータ |
| **ArtifactRepository** | Artifact を保存・取得する抽象インターフェイス |

---

## 📁 Directory Structure

```
ai-helper/
├─ ai_helper/core/       # Pipeline エンジンの中核処理
├─ ai_helper/nodes/      # 各種ノード実装
├─ ai_helper/runtimes/   # AI モデル・外部サービス接続
├─ ai_helper/pipelines/  # パイプライン定義
├─ ai_helper/app/        # CLI / Web UI
├─ ai_helper/utils/      # 汎用ユーティリティ
├─ ai_helper/db/         # データベース関連
└─ ai_helper/config/     # 設定ファイル
```

---

## 🛠️ Getting Started

### Install

```bash
git clone https://github.com/KiharaTakahiro/ai-helper.git
cd ai-helper
poetry install
poetry shell
```

---

## 🧪 Usage Examples

### Python でパイプラインを実行

```python
from ai_helper.core.context import Context
from ai_helper.infra.storage.local_repository import LocalArtifactRepository
from ai_helper.core.registry import register_node
from ai_helper.nodes.demo import SampleNode

# ノード定義・登録例
register_node("sample", SampleNode)

ctx = Context()
# パイプライン実行例
pipeline = ...  # pipelines/ 以下に定義された PipelineDefinition の読み込み
pipeline.run(ctx)
```

### API サーバ実行（FastAPI）

```bash
uvicorn ai_helper.api.main:app --reload
```

#### Pipeline 実行 API

```
POST /pipeline/run/demo
```

このエンドポイントを叩くと、デフォルトの SQLite DB に実行履歴が記録されます。

---

## 📌 Next Roadmap (TODO)

- Node plugin system の構築
- パイプライングラフ UI の追加
- 分散実行サポート
- GPU Node / 外部サービス連携ノードの追加

---

## ⛓ Related Docs

- 設計仕様: `design.md`
- コーディングスタイル: `CODE_STYLE.md`