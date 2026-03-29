# ai-helper Architecture

ai-helper は AI処理パイプラインを構築・実行するためのフレームワークである。

主な目的は以下の通り。

- AI処理をパイプラインとして構造化する
- Node単位で処理を分離する
- Artifactを用いてNode間データを管理する
- 実行エンジンを抽象化する

このドキュメントでは ai-helper のアーキテクチャと設計思想を説明する。

---

# 1. 基本アーキテクチャ

ai-helper は以下のレイヤー構造で構成される。

```
CLI / API
   ↓
Executor
   ↓
Core
   ↓
Storage
```

各レイヤーの責務は以下の通り。

## CLI / API

パイプライン実行のエントリーポイントを提供する。

主な役割

- Pipeline定義読み込み
- Pipeline生成
- Executor呼び出し

## Executor

PipelineおよびNodeの実行を管理する。

主な役割

- Node実行
- 実行順序管理
- 実行状態管理

## Core

フレームワークのコア概念を定義する。

主な要素

- Pipeline
- Node
- Artifact
- Context
- Registry

## Storage

Artifactの保存を担当する。

ストレージ実装は抽象化されており、
ローカルストレージ・クラウドストレージなどに置き換え可能。

---

# 2. Pipelineモデル

ai-helperではAI処理を **Pipeline** として表現する。

PipelineはNodeの集合であり、
Node間の依存関係はDAG（Directed Acyclic Graph）として管理される。

```
Pipeline
  ↓
Node
  ↓
Artifact
```

Pipelineは以下を管理する。

- Nodeの集合
- Node依存関係
- 実行順序

Pipeline自体は **処理ロジックを持たず**、
構造のみを定義する。

実際の実行はExecutorが担当する。

---

# 3. Nodeモデル

Nodeはパイプライン内の処理単位である。

Nodeは以下の責務を持つ。

- Artifactを入力として受け取る
- 処理を実行する
- 新しいArtifactを生成する

処理モデル

```
Input Artifact
      ↓
     Node
      ↓
Output Artifact
```

すべてのNodeは `run()` メソッドを実装する必要がある。

例

```python
class ExampleNode(Node):

    def execute(self, ctx, repo):
        # Node処理
        pass
```

---

# 4. Artifactモデル

ArtifactはNodeの実行結果を表すデータオブジェクトである。

主な役割

- Node間データ共有
- 処理結果保存
- パイプライン状態管理

Artifactの実体は **Repositoryに保存される。**

ContextはArtifactの **IDのみ** を保持する。

```
Node
 ↓
Artifact
 ↓
Repository
```

この設計により

- 大容量データ対応
- 再実行
- キャッシュ

などが容易になる。

---

# 5. Context

Contextはパイプライン実行中の状態を保持するオブジェクトである。

主な役割

- Artifact ID管理
- Node間データ共有
- 実行状態管理

例

```
Context.artifacts

{
  "input_video": artifact_id
}
```

Contextは **実データを持たず**
Artifactの参照のみを管理する。

---

# 6. Executor

ExecutorはPipelineの実行エンジンである。

責務

- Node実行
- 依存関係解決
- 実行順序管理

実行フロー

```
PipelineExecutor

↓ DAG解析

↓ Node順序決定

↓ Node実行

↓ Artifact生成
```

PipelineとExecutorを分離することで

- Pipeline定義
- 実行ロジック

を独立させている。

---

# 7. NodeRegistry

NodeRegistryはNode typeからNodeクラスを解決する仕組みである。

例

```
type: video_input
```

↓

```
VideoInputNode
```

この仕組みにより以下を実現する。

- YAMLパイプライン
- Plugin Node
- 動的Nodeロード

---

# 8. Pipeline定義

ai-helperではPipelineを以下の方法で定義できる。

## Python定義

```python
pipeline = Pipeline(...)
```

## YAML定義

```yaml
nodes:
  - video_input
  - frame_extract
```

YAMLは簡易パイプライン、
Pythonは複雑なパイプライン定義に適している。

---

# 9. ディレクトリ構造

```
ai_helper/

app/
  cli/

core/
  pipeline/
  node/
  artifact/
  context/
  registry/

infra/
  storage/
```

各ディレクトリの責務

## app

アプリケーションエントリーポイント

例

- CLI
- API

## core

フレームワークコア

例

- Pipeline
- Node
- Artifact
- Context

## infra

インフラ実装

例

- Storage
- Database

---

# 10. 実行フロー

パイプライン実行の基本フロー

```
CLI

↓ Pipeline定義読み込み

↓ Pipeline生成

↓ Executor

↓ Node実行

↓ Artifact生成
```

---

# 11. 用語

|用語|説明|
|---|---|
|Node|処理単位|
|Artifact|Node実行結果|
|Pipeline|Node集合|
|Executor|実行エンジン|
|Registry|Node解決機構|

---

# 12. 設計思想

ai-helperの設計は以下の原則に基づく。

## 処理はNode単位で分離する

パイプラインは小さな処理単位に分割する。

## Node間データはArtifactで管理する

Node間のデータ依存関係を明確にする。

## PipelineとExecutorを分離する

Pipelineは構造、
Executorは実行を担当する。

## Storage実装を抽象化する

ストレージを差し替え可能にする。

---

# 13. 拡張性

ai-helperは以下の拡張を想定している。

- Plugin Node
- 分散実行
- キャッシュ
- GPU処理
- 外部ストレージ

これらはExecutorおよびRegistryを拡張することで実現可能である。