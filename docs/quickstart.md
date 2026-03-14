# Quickstart

このガイドでは ai-helper を使って
簡単な Pipeline を実行する方法を説明する。

---

# 1. 前提条件

ai-helper を使用するには以下の環境が必要。

|項目|推奨|
|---|---|
|Python|3.10 以上|
|pip|最新版|
|OS|Linux / macOS / Windows|

Pythonバージョン確認

```bash
python --version
```

---

# 2. インストール

## pip を使う場合

```bash
pip install ai-helper
```

またはリポジトリを clone する。

```bash
git clone https://github.com/<your-repo>/ai-helper
cd ai-helper
pip install -e .
```

---

# 3. pyenv を使う場合

Pythonバージョンを固定する場合は
pyenv の使用を推奨する。

例

```bash
pyenv install 3.11
pyenv local 3.11
```

確認

```bash
python --version
```

---

# 4. Poetry を使う場合

Poetryを使って開発する場合。

Poetry インストール

```bash
pip install poetry
```

依存関係インストール

```bash
poetry install
```

仮想環境に入る

```bash
poetry shell
```

CLI実行

```bash
poetry run ai-helper run pipeline.yaml
```

---

# 5. Pipeline定義

ai-helperでは Pipeline を YAML で定義できる。

例

```yaml
pipeline:

  nodes:

    - id: input
      type: text_input

    - id: upper
      type: uppercase
      depends_on:
        - input
```

---

# 6. Pipeline実行

CLIから Pipeline を実行する。

```bash
ai-helper run pipeline.yaml
```

実行フロー

```
CLI
 ↓
Pipeline読み込み
 ↓
Executor
 ↓
Node実行
 ↓
Artifact生成
```

---

# 7. Nodeの追加

独自 Node を作成することもできる。

例

```python
from ai_helper.core.node import Node


class UppercaseNode(Node):

    def run(self, ctx, repo):

        input_id = ctx.artifacts["input"]

        artifact = repo.load(input_id)

        result = artifact.data.upper()

        output_id = repo.save(result)

        ctx.artifacts["output"] = output_id
```

---

# 8. 開発モードでインストール

Node開発を行う場合は editable install を推奨する。

```bash
pip install -e .
```

これによりコード変更が即座に反映される。

---

# 9. よくある問題

## Pythonバージョンエラー

例

```
ModuleNotFoundError
```

Pythonバージョンを確認する。

```bash
python --version
```

---

## Poetry環境でCLIが見つからない

Poetry環境では以下で実行する。

```bash
poetry run ai-helper
```

---

## 依存関係エラー

依存関係が壊れている場合は
再インストールする。

```bash
pip install -e .
```

または

```bash
poetry install
```

---

# 10. 次のステップ

詳細なドキュメントはこちら。

- architecture.md
- node_development.md
- pipeline_definition.md