# Node Development Guide

このドキュメントでは ai-helper における Node の開発方法を説明する。

Node はパイプラインの処理単位であり、
入力 Artifact を受け取り、新しい Artifact を生成する。

---

# 1. Nodeとは

Nodeはパイプライン内の処理単位である。

Nodeの基本モデル

```
Input Artifact
      ↓
     Node
      ↓
Output Artifact
```

Nodeは **ビジネスロジックのみを担当する。**

Nodeは以下を直接扱わない。

- Pipeline構造
- 実行順序
- Storage実装

これらは Executor が管理する。

---

# 2. Nodeの基本構造

すべてのNodeは `Node` クラスを継承する。

例

```python
from ai_helper.core.node import Node


class ExampleNode(Node):
    """
    ExampleNode はサンプルNodeである。
    """

    def run(self, ctx, repo):
        """
        Node処理を実行する。

        Parameters
        ----------
        ctx : Context
            パイプライン実行コンテキスト

        repo : ArtifactRepository
            Artifact保存リポジトリ
        """

        pass
```

---

# 3. runメソッド

Nodeの処理は `run()` メソッドに実装する。

```
def run(self, ctx, repo):
```

引数

|引数|説明|
|---|---|
|ctx|実行コンテキスト|
|repo|Artifact保存リポジトリ|

---

# 4. Artifactの取得

Nodeは Context から Artifact ID を取得する。

例

```python
artifact_id = ctx.artifacts["input_image"]
```

Artifact本体は Repository から取得する。

```python
artifact = repo.load(artifact_id)
```

---

# 5. Artifactの保存

Nodeの処理結果は Artifact として保存する。

例

```python
new_artifact = Artifact(data=result)

artifact_id = repo.save(new_artifact)
```

---

# 6. Context更新

生成した Artifact ID を Context に登録する。

```python
ctx.artifacts["output_image"] = artifact_id
```

---

# 7. Node実装例

例：テキストを大文字に変換するNode

```python
class UppercaseNode(Node):

    def run(self, ctx, repo):

        input_id = ctx.artifacts["input_text"]

        artifact = repo.load(input_id)

        text = artifact.data

        result = text.upper()

        new_artifact = Artifact(data=result)

        output_id = repo.save(new_artifact)

        ctx.artifacts["output_text"] = output_id
```

---

# 8. Node設計ルール

Node実装には以下のルールを守る。

## 1 Node = 1 処理

Nodeは単一の処理のみを担当する。

悪い例

```
動画入力
↓
フレーム抽出
↓
顔検出
```

良い例

```
VideoInputNode
FrameExtractNode
FaceDetectNode
```

---

## Nodeは副作用を持たない

Nodeは以下を直接操作してはいけない。

- ファイルシステム
- DB
- ネットワーク

必要な場合は Artifact を使用する。

---

## Nodeは状態を持たない

Nodeは内部状態を保持しない。

すべての状態は

- Context
- Artifact

で管理する。

---

# 9. Node登録

Nodeは Registry に登録する必要がある。

例

```python
registry.register(
    "uppercase",
    UppercaseNode
)
```

YAML Pipeline では type 名で Node を解決する。

```
type: uppercase
```

---

# 10. Nodeファイル配置

Nodeは以下のディレクトリに配置する。

```
ai_helper/
  nodes/
```

例

```
nodes/
  image/
  text/
  video/
```

---

# 11. Node命名規則

Nodeクラス名は以下の形式にする。

```
<Function>NameNode
```

例

|処理|クラス名|
|---|---|
|画像リサイズ|ResizeImageNode|
|動画入力|VideoInputNode|
|顔検出|FaceDetectNode|

---

# 12. Nodeテスト

Nodeは単体テストを書く。

テスト内容

- Artifact入力
- run()実行
- Artifact出力確認

例

```
tests/nodes/test_uppercase_node.py
```

---

# 13. エラー処理

Nodeは例外を適切に処理する。

例

```python
if artifact is None:
    raise ValueError("input artifact not found")
```

Executorは例外を受け取り、
Pipeline実行を停止する。

---

# 14. ログ

Nodeはログ出力を行うことができる。

例

```python
logger.info("processing image")
```

---

# 15. Node設計の原則

ai-helperでは以下の原則を採用する。

## 小さなNode

Nodeは小さく保つ。

## Nodeの再利用

同じNodeを複数のPipelineで使えるようにする。

## Nodeの独立性

Nodeは他Nodeの内部実装に依存しない。

---

# 16. Node拡張

将来的に以下の機能追加を想定している。

- GPU Node
- Async Node
- Distributed Node
- Streaming Node

Nodeインターフェースはこれらの拡張に対応できるよう設計されている。