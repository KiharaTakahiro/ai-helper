# ai-helper 設計ドキュメント

このドキュメントは ai-helper のコア設計情報をまとめたものです。  
GitHub 上で Mermaid がそのままレンダリングされる形式になっています。

---

## 1. プロジェクト概要

**ai-helper** は、複数の AI 処理をパイプラインとして組み合わせ、  
自動化・再現可能な AI ワークフローを実現する軽量エンジンです。

用途例：

- 動画生成パイプライン
- face swap / voice swap
- テキスト生成・データ処理自動化
- 外部サービスやモデルの連携

---

## 2. 基本概念

| 用語 | 説明 |
|------|------|
| Pipeline | Node を順番に実行する処理の単位 |
| Node | Pipeline 内の処理単位（入力→処理→出力） |
| Context | Node 間で共有される実行状態 |
| Artifact | Node の出力データの参照（ID 形式） |
| ArtifactRepository | Artifact の保存・取得を抽象化する層 |

---

## 3. Pipeline 実行フロー

\```mermaid
flowchart TD
    A[PipelineDefinition] -->|取得| B[NodeFactory]
    B -->|Node 生成| C[Pipeline]
    C --> D[Context 作成]
    D --> E[Pipeline.run()]
    E --> F{Node1, Node2, ...}
    F --> G[Node1 実行]
    F --> H[Node2 実行]
    F --> I[NodeN 実行]
    G --> J[Artifact 保存]
    H --> J
    I --> J
\```

---

## 4. Node 実行イメージ

\```mermaid
flowchart TD
    VI[VideoInputNode]
    FE[FrameExtractNode]
    FS[FaceSwapNode]
    RN[RenderNode]

    VI --> FE --> FS --> RN
\```

### Node 内部の処理フロー

\```mermaid
flowchart LR
    A[inputs] --> B[run() 処理] --> C[outputs]
    B --> D[ArtifactRepository.save()]
    C --> E[Context に出力ID登録]
\```

---

## 5. Context と Artifact の関係

\```mermaid
flowchart TD
    subgraph Pipeline Context
        CTX[Context]
    end
    CTX -->|artifact_id| AR[ArtifactRepository]
    AR -->|保存/取得| ST[(Storage: local/S3/MinIO/DB)]
\```

---

## 6. Node 定義ルール

- Node は必ず以下を定義する：
  - `inputs`：必要な Artifact 名
  - `outputs`：出力する Artifact 名
- `run()` 内で ArtifactRepository を使って入出力を取得/保存
- Node は副作用を避け、外部状態は ArtifactRepository 経由で管理
- Node は順序や依存関係を PipelineDefinition で明示

### Node 定義例（Python）

\```python
class FrameExtractNode(Node):
    inputs = ["video"]
    outputs = ["frames"]

    def run(self, context: Context):
        video = self.get_input("video")
        frames = extract_frames(video)
        self.save_output("frames", frames)
\```

---

## 7. Artifact 定義と保存戦略

- Artifact は「データ参照」＋「メタデータ」を保持
- 実データは Storage 層に保存
- ArtifactRepository は保存・取得・更新を抽象化
- 将来的にローカル / S3 / MinIO / DB / Redis を切り替え可能

\```mermaid
flowchart TD
    Context -->|artifact_id| Repo[ArtifactRepository]
    Repo -->|保存/取得| Storage[(Local/S3/MinIO/DB)]
\```

---

## 8. PipelineDefinition

- PipelineDefinition は以下の情報を保持

| 属性 | 説明 |
|------|------|
| id | Pipeline 識別子 |
| nodes[] | NodeDefinition の配列（順序情報含む） |

NodeDefinition 例：

\```json
{
  "type": "frame_extract",
  "config": {"param1": "value1"},
  "order": 2
}
\```

- PipelineDefinition はファイルや DB からロード可能
- Node の依存関係は `inputs`/`outputs` で自動解決

---

## 9. 拡張方針 / 将来計画

- Node plugin system の構築
- パイプライングラフ UI（Web 表示）
- 分散実行対応
- GPU Node / 外部サービス連携ノード
- Artifact バックエンドの多様化

---

## 10. Mermaid の利用について

- このドキュメントは GitHub 上でそのまま Mermaid をレンダリング可能  
- Pipeline / Node / Artifact 関係を視覚化することで理解しやすい設計書として利用

---

## 参考資料

- 設計原案: design.md
- コードベース: ai_helper/core/ / ai_helper/nodes/ / ai_helper/runtimes/