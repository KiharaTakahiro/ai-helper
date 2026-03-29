"""
ノード実行エンジンを提供するモジュール。

NodeExecutor は「単一ノードの実行」に特化したクラスであり、
Pipeline 全体の制御とは完全に分離されている。

主な用途：
- Pipeline 実行時の内部利用
- Node 単体テスト
- デバッグ用途
"""

from typing import Dict
import datetime
import time
import tracemalloc

from ai_helper.core.context import Context
from ai_helper.core.node import Node
from ai_helper.core.repository.artifact_repository import ArtifactRepository
import logging

logger = logging.getLogger(__name__)

class NodeExecutor:
    """
    単一ノードの実行を担当するクラス。

    -----------------------------
    ■ このクラスの役割
    -----------------------------
    NodeExecutor は以下を責務とする：

    1. Node インスタンスの生成（Definition からの変換）
    2. Node.run() の実行
    3. 入出力アーティファクトの型チェック
    4. 実行ログの記録（DB）
    5. リトライ処理
    6. 実行時間・メモリ使用量の計測

    -----------------------------
    ■ Pipeline との関係
    -----------------------------
    Pipeline は「どの順番で実行するか」を決める

    NodeExecutor は「1つのノードをどう実行するか」を担当する

    → 責務を明確に分離している

    -----------------------------
    ■ Attributes
    -----------------------------
    artifact_repository (ArtifactRepository):
        アーティファクト保存・取得用

    db_session:
        DBセッション（ログ記録用）

    node_run_repository:
        ノード単位の実行ログ保存

    pipeline_run_repository:
        パイプライン単位の実行ログ参照用
    """

    def __init__(self, artifact_repository: ArtifactRepository, db_session=None):
        """
        NodeExecutor を初期化する。

        Args:
            artifact_repository (ArtifactRepository):
                アーティファクト管理リポジトリ

            db_session:
                DBセッション（任意）
        """
        self.artifact_repository = artifact_repository
        self.db_session = db_session

        self.node_run_repository = None
        self.pipeline_run_repository = None

        # DBセッションがある場合のみリポジトリを生成
        if db_session is not None:
            from ai_helper.repository import NodeRunRepository, PipelineRunRepository

            self.node_run_repository = NodeRunRepository(db_session)
            self.pipeline_run_repository = PipelineRunRepository(db_session)

    def execute(
        self,
        node_or_definition,
        execution_context: Context,
        pipeline_run_id: str | None = None,
    ) -> Dict[str, str]:
        """
        単一ノードの実行を行うメインメソッド。

        ==================================================
        ■ このメソッドの役割
        ==================================================
        このメソッドは「1つのノードを安全に実行するための全処理」をまとめている。

        単に node.run() を呼ぶだけではなく、以下をすべて面倒見る：

        - NodeDefinition → Nodeインスタンス生成
        - 入力の型チェック（事前検証）
        - 実行
        - 出力の型チェック（事後検証）
        - リトライ制御（失敗時）
        - GPU要件チェック
        - 実行時間・メモリ計測
        - 実行ログ（DB）記録

        ==================================================
        ■ 処理の全体フロー（超重要）
        ==================================================
        ① Nodeインスタンス準備
        ② 実行メトリクス計測開始
        ③ DBログ開始（必要な場合）
        ④ リトライ付き実行ループ
            - GPUチェック
            - 入力型チェック
            - node.run() 実行
            - 出力型チェック
        ⑤ メトリクス計測終了
        ⑥ 成功ログ更新
        ⑦ 出力アーティファクト返却

        ==================================================
        ■ なぜこの設計なのか？
        ==================================================
        Node自体は「処理ロジックのみ」を持たせたい。

        そのため以下はすべてExecutor側で吸収している：
        - リトライ
        - ログ
        - 型検証
        - メトリクス

        → Nodeは純粋な処理だけ書けばよい（責務分離）

        ==================================================
        ■ Args
        ==================================================
        node_or_definition:
            Nodeインスタンス、またはNodeDefinition。

            - NodeDefinitionの場合：
                → ここでインスタンス生成する
            - Nodeの場合：
                → そのまま使用する

        execution_context (Context):
            実行コンテキスト。
            アーティファクト（入出力データ）はすべてここに保存される。

        pipeline_run_id (str | None):
            パイプライン実行ID。
            DBログと紐づけるために使用する。

        ==================================================
        ■ Returns
        ==================================================
        Dict[str, str]:
            出力アーティファクト名 → アーティファクトID

        ==================================================
        ■ Raises
        ==================================================
        Exception:
            リトライ回数を超えても失敗した場合に例外を再送出する
        """

        # ==================================================
        # ① Nodeインスタンスの準備
        # ==================================================
        # NodeDefinition が渡された場合は、実行可能な Node に変換する
        if not isinstance(node_or_definition, Node):
            from ai_helper.core.registry.factory import NodeFactory

            node_factory = NodeFactory()

            node_instance = node_factory.create(
                node_or_definition.node_type,
                node_or_definition.config
            )

            # 実行時に definition 情報を参照するため保持
            node_instance.definition = node_or_definition
        else:
            # すでに Node インスタンスならそのまま使用
            node_instance = node_or_definition

        # --------------------------------------------------
        # ノードID取得（ログやデバッグ用）
        # --------------------------------------------------
        node_id = (
            getattr(node_instance.definition, "node_id", None)
            if hasattr(node_instance, "definition")
            else node_instance.__class__.__name__
        )
        logger.info(f"[開始] ノード実行: {node_id}")

        # ==================================================
        # ② 実行メトリクス計測開始
        # ==================================================
        # 実行時間測定開始（高精度タイマー）
        execution_start_time = time.perf_counter()

        # メモリ使用量の追跡開始
        tracemalloc.start()

        # ==================================================
        # ③ DBログ開始（オプション）
        # ==================================================
        node_run_record = None

        # DBが有効な場合のみログを記録する
        if self.node_run_repository and pipeline_run_id:
            node_run_record = self.node_run_repository.create(
                pipeline_run_id,
                node_instance.__class__.__name__
            )

            # 実行開始状態に更新
            self.node_run_repository.update_status(
                node_run_record.id,
                "RUNNING"
            )

        # ==================================================
        # ④ リトライ付き実行ループ
        # ==================================================
        current_attempt_count = 0

        while True:
            try:
                # ------------------------------------------
                # GPU要件チェック
                # ------------------------------------------
                # NodeがGPU必須かどうか確認
                requires_gpu = getattr(
                    node_instance.definition,
                    "requires_gpu",
                    False
                )

                # GPUが必要なのに使用不可ならスキップ
                if requires_gpu and not _is_gpu_available():
                    if self.node_run_repository and node_run_record:
                        self.node_run_repository.update_status(
                            node_run_record.id,
                            "SKIPPED",
                            finished_at=datetime.datetime.now(datetime.UTC),
                        )
                    return {}

                # ------------------------------------------
                # 入力アーティファクト型チェック（実行前）
                # ------------------------------------------
                # Nodeが期待する型と一致しているか確認
                self._validate_input_types(node_instance, execution_context)

                # ------------------------------------------
                # ノードの本処理を実行
                # ------------------------------------------
                # 実際のビジネスロジックはここ
                node_instance.run(
                    execution_context,
                    self.artifact_repository
                )

                # ------------------------------------------
                # 出力アーティファクト型チェック（実行後）
                # ------------------------------------------
                self._validate_output_types(node_instance, execution_context)

                # 成功したのでループ終了
                break

            except Exception as execution_error:
                # ------------------------------------------
                # 失敗時処理（リトライ制御）
                # ------------------------------------------
                current_attempt_count += 1

                max_retry_count = getattr(
                    node_instance.definition,
                    "retry_count",
                    0
                )

                # リトライ上限を超えた場合は失敗
                if current_attempt_count > max_retry_count:
                    if self.node_run_repository and node_run_record:
                        self.node_run_repository.update_status(
                            node_run_record.id,
                            "FAILED",
                            finished_at=datetime.datetime.now(datetime.UTC),
                        )

                    # 元の例外をそのまま投げる
                    raise execution_error

                # リトライ前に待機（バックオフ的な役割）
                retry_delay_seconds = getattr(
                    node_instance.definition,
                    "retry_delay",
                    0
                )

                time.sleep(retry_delay_seconds)

        # ==================================================
        # ⑤ メトリクス計測終了
        # ==================================================
        _ , peak_memory_usage = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        total_execution_time = time.perf_counter() - execution_start_time

        # ==================================================
        # ⑥ 成功ログ更新
        # ==================================================
        if self.node_run_repository and node_run_record:
            self.node_run_repository.update_status(
                node_run_record.id,
                "SUCCESS",
                finished_at=datetime.datetime.now(datetime.UTC),
                execution_time=total_execution_time,
                memory_usage=peak_memory_usage,
            )

        # ==================================================
        # ⑦ 出力アーティファクト収集
        # ==================================================
        # Nodeが定義している出力名を取得
        if isinstance(node_instance.outputs, dict):
            output_name_list = list(node_instance.outputs.keys())
        else:
            output_name_list = list(node_instance.outputs)

        logger.info(f"[完了] ノード実行: {node_id}")
        # Contextから該当アーティファクトIDを取得して返却
        return {
            output_name: execution_context.artifacts.get(output_name)
            for output_name in output_name_list
        }

    def _validate_input_types(self, node_instance: Node, execution_context: Context):
        """
        ノード実行前に「入力アーティファクトの型」を検証する内部メソッド。

        ==================================================
        ■ このメソッドの役割
        ==================================================
        Node が実行される前に、

            「その Node が必要としている入力データが
            正しく存在し、かつ正しい型であるか？」

        をチェックする。

        これを行うことで、以下の問題を事前に防ぐ：

        - 必要な入力が存在しない（None になる）
        - 想定外のデータ型で処理が壊れる
        - 後続処理で意味不明なエラーになる

        ==================================================
        ■ なぜここでチェックするのか？
        ==================================================
        Node.run() の中でチェックすると：

        - 各Nodeに同じチェックを書く必要がある（重複）
        - 実装者によって品質がバラバラになる

        → Executor側で統一的にチェックすることで安全性を担保する

        ==================================================
        ■ Args
        ==================================================
        node_instance (Node):
            実行対象のノード

        execution_context (Context):
            アーティファクトを保持しているコンテキスト

            例：
                execution_context.artifacts = {
                    "image": "artifact_id_123"
                }

        ==================================================
        ■ Raises
        ==================================================
        ValueError:
            必要な入力アーティファクトが存在しない場合

        TypeError:
            入力アーティファクトの型が期待と異なる場合
        """

        # --------------------------------------------------
        # 入力定義が「型付き（dict）」である場合のみチェックを行う
        # --------------------------------------------------
        # list形式の場合は型情報がないため、このメソッドでは何もしない
        if not isinstance(node_instance.inputs, dict):
            return

        # --------------------------------------------------
        # ArtifactRepository に metadata_repo が存在する場合のみ型チェック可能
        # --------------------------------------------------
        # metadata_repo がない場合：
        # → 型情報を取得できないため、型チェックはスキップする
        if not getattr(self.artifact_repository, "metadata_repo", None):
            return

        # --------------------------------------------------
        # 各入力アーティファクトについてチェックを行う
        # --------------------------------------------------
        for input_name, expected_type in node_instance.inputs.items():

            # ------------------------------------------
            # ① ContextからアーティファクトIDを取得
            # ------------------------------------------
            artifact_id = execution_context.artifacts.get(input_name)

            # ------------------------------------------
            # ② 入力が存在するかチェック
            # ------------------------------------------
            if artifact_id is None:
                # ログ出力（デバッグ用）
                logger.error(
                    f"入力アーティファクト不足: '{input_name}' がContext内に存在しません"
                )

                # 例外として処理を止める
                raise ValueError(
                    f"入力アーティファクト不足: '{input_name}'"
                )

            # ------------------------------------------
            # ③ メタデータ取得（型情報を取得）
            # ------------------------------------------
            artifact_metadata = self.artifact_repository.metadata_repo.get(artifact_id)

            # ------------------------------------------
            # ④ 型チェック
            # ------------------------------------------
            # metadata が存在しない場合はチェック不能なのでスキップ
            if artifact_metadata is None:
                continue

            actual_type = artifact_metadata.type

            # 型が一致しない場合はエラー
            if actual_type != expected_type:
                logger.error(
                    f"入力アーティファクト型不一致: '{input_name}' は '{actual_type}' だが '{expected_type}' を期待"
                )

                raise TypeError(
                    f"型不一致: '{input_name}' は '{actual_type}' だが '{expected_type}' を期待"
                )

    def _validate_output_types(self, node_instance: Node, execution_context: Context):
        """
        ノード実行後に「出力アーティファクトの型」を検証する内部メソッド。

        ==================================================
        ■ このメソッドの役割
        ==================================================
        Node.run() の実行が完了した後に、

            「Nodeが宣言した出力が正しく生成されているか？」
            「その出力の型は定義通りか？」

        をチェックする。

        ==================================================
        ■ なぜ必要なのか？
        ==================================================
        Node の実装ミスで以下のような問題が発生する可能性がある：

        - 出力を set_artifact し忘れる
        - 間違った名前で出力する
        - 型が違うデータを出力する

        → これを検知しないと：
            ・後続Nodeで原因不明のエラーになる
            ・デバッグが非常に困難になる

        そのため、Executor側で「契約違反」を検出する

        ==================================================
        ■ 入力チェックとの違い
        ==================================================
        _validate_input_types:
            → 実行前チェック（前提条件の確認）

        _validate_output_types:
            → 実行後チェック（結果の保証）

        ==================================================
        ■ 前提知識（初心者向け）
        ==================================================
        Node.outputs は以下のどちらか：

        ① dict形式（推奨）
            {
                "output_name": "expected_type"
            }

            → 型チェックを行う

        ② list形式
            ["output_name"]

            → 型チェックは行わない（存在チェックのみ）

        ==================================================
        ■ Args
        ==================================================
        node_instance (Node):
            実行済みのノード

        execution_context (Context):
            アーティファクトを保持するコンテキスト

        ==================================================
        ■ Raises
        ==================================================
        ValueError:
            出力アーティファクトが生成されていない場合

        TypeError:
            出力アーティファクトの型が期待と異なる場合
        """

        # --------------------------------------------------
        # 出力定義が dict の場合のみ型チェックを行う
        # --------------------------------------------------
        # list形式の場合は型情報が無いためスキップ
        if not isinstance(node_instance.outputs, dict):
            return

        # --------------------------------------------------
        # metadata_repo が存在しない場合は型チェックできない
        # --------------------------------------------------
        # → 型チェックはスキップする（存在チェックのみになる）
        if not getattr(self.artifact_repository, "metadata_repo", None):
            return

        # --------------------------------------------------
        # 各出力について検証を行う
        # --------------------------------------------------
        for output_name, expected_output_type in node_instance.outputs.items():

            # ------------------------------------------
            # ① Contextから出力アーティファクトIDを取得
            # ------------------------------------------
            artifact_id = execution_context.artifacts.get(output_name)

            # ------------------------------------------
            # ② 出力が存在するかチェック
            # ------------------------------------------
            if artifact_id is None:
                # Nodeが出力を生成していない → 実装ミス
                raise ValueError(
                    f"出力不足: '{output_name}' が生成されていません"
                )

            # ------------------------------------------
            # ③ メタデータ取得（型情報取得）
            # ------------------------------------------
            artifact_metadata = self.artifact_repository.metadata_repo.get(artifact_id)

            # ------------------------------------------
            # ④ 型チェック
            # ------------------------------------------
            # metadataが無い場合はチェック不能なのでスキップ
            if artifact_metadata is None:
                continue

            actual_output_type = artifact_metadata.type

            # 型不一致 → 明確なバグ
            if actual_output_type != expected_output_type:
                raise TypeError(
                    f"出力型不一致: '{output_name}' は '{actual_output_type}' だが '{expected_output_type}' を期待"
                )

def _is_gpu_available():
    """
    GPU（CUDA）が利用可能かどうかを判定する。

    Returns:
        bool:
            利用可能なら True
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False