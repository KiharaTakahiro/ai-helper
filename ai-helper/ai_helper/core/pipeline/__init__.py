"""
Pipeline execution engine.

Pipeline は Node の DAG (Directed Acyclic Graph) を表す。

構造

Pipeline
   ↓
Node
   ↓
Artifact

Node は Artifact を入力として受け取り
新しい Artifact を生成する。

Pipeline は

1 依存関係解決
2 実行順序決定
3 Node実行

を管理する。
"""

import datetime
import hashlib
import json
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from typing import Dict, List

from ai_helper.core.context import Context
from ai_helper.core.repository.artifact_repository import ArtifactRepository
from ai_helper.core.node import Node

logger = logging.getLogger(__name__)


class Pipeline:
    """
    パイプライン処理クラス。

    ノードの依存関係（DAG）を解決し、
    適切な順序で Node を実行する責務を持つ。

    Attributes:
        nodes (List[Node]):
            実行対象のノード一覧（トポロジカル順）

        cache (Dict):
            ノード実行結果キャッシュ
            key -> outputs

        _node_map (Dict[str, Node]):
            node_id → Node インスタンス
    """

    def __init__(self, nodes: List[Node]):
        """
        Pipeline を初期化する。

        Args:
            nodes (List[Node]):
                実行対象のノード一覧
        """
        self.nodes = nodes
        self.cache = {}

        # node_id → node のマッピングを事前構築
        self._node_map = {
            getattr(n, 'definition', None).node_id: n
            for n in nodes if hasattr(n, 'definition')
        }

    @classmethod
    def from_definition(
        cls,
        pipeline_definition,
        node_factory=None,
        initial_artifacts: Dict[str, str] = None
    ):
        """
        PipelineDefinition（設定データ）から、実行可能な Pipeline インスタンスを生成する。

        このメソッドは「設定ファイル（Definition）」を元に、
        実際に実行できる Pipeline オブジェクトを構築する役割を持つ。

        ------------------------------------------------------------
        ■ このメソッドがやっていること（重要）
        ------------------------------------------------------------
        1. ノード間の依存関係（DAG）を構築する
        2. 実行順序をトポロジカルソートで決定する
        3. Node インスタンスを生成する
        4. 入力アーティファクトの整合性をチェックする（静的検証）

        ------------------------------------------------------------
        ■ なぜこの処理が必要か
        ------------------------------------------------------------
        PipelineDefinition はあくまで「設定」であり、
        そのままでは実行できない。

        そのため以下を解決する必要がある：
        - どの順番で実行するか（依存関係）
        - 実際の Node オブジェクト生成
        - 入力データが存在するかのチェック

        ------------------------------------------------------------
        Args:
            pipeline_definition:
                Pipeline の構成情報（ノード一覧や依存関係を含む）

            node_factory:
                Node を生成するための Factory
                未指定の場合はデフォルトの NodeFactory を使用する

            initial_artifacts (Dict[str, str], optional):
                外部から渡される初期アーティファクト
                （例：最初の入力データ）

        ------------------------------------------------------------
        Returns:
            Pipeline:
                実行可能な Pipeline インスタンス

        ------------------------------------------------------------
        Raises:
            ValueError:
                必要な入力アーティファクトが存在しない場合

            TypeError:
                アーティファクトの型が一致しない場合
        """
        from ai_helper.core.registry.factory import NodeFactory

        # ------------------------------------------------------------
        # NodeFactory の準備
        # ------------------------------------------------------------
        # node_factory が渡されていない場合はデフォルトを使用する
        node_factory = node_factory or NodeFactory()

        # Pipeline インスタンスを一旦空で作成
        pipeline = cls([])

        # ------------------------------------------------------------
        # 1. 依存関係マップの構築
        # ------------------------------------------------------------
        # dependency_map の形式：
        #   {
        #       "nodeA": ["nodeB", "nodeC"],  ← nodeA は nodeB, nodeC に依存
        #       "nodeB": [],
        #   }
        #
        # この情報を元に実行順序を決定する
        dependency_map = pipeline._build_dependency_map(
            pipeline_definition.nodes
        )

        # ------------------------------------------------------------
        # 2. 実行順序の決定（トポロジカルソート）
        # ------------------------------------------------------------
        # dependency_map を元に、
        # 「依存関係を満たす順序」に並べる
        #
        # 例：
        #   A → B → C
        #   の場合、[A, B, C] の順になる
        sorted_node_ids = pipeline._topological_sort(dependency_map)

        # ------------------------------------------------------------
        # 3. Node インスタンス生成
        # ------------------------------------------------------------
        # 実際に実行する Node オブジェクトを作る
        node_instances: List[Node] = []

        # すでに生成された出力（artifact）を記録する
        # → 後続ノードの入力チェックに使用する
        produced_artifacts = {}

        # ------------------------------------------------------------
        # 4. ノードを順番に処理
        # ------------------------------------------------------------
        for node_id in sorted_node_ids:

            # --------------------------------------------------------
            # 対応する NodeDefinition を取得
            # --------------------------------------------------------
            # pipeline_definition.nodes の中から
            # node_id が一致するものを探す
            node_definition = next(
                filter(
                    lambda definition: definition.node_id == node_id,
                    pipeline_definition.nodes
                )
            )

            # --------------------------------------------------------
            # Node インスタンス生成
            # --------------------------------------------------------
            # node_type と config を元に Node を生成する
            node_instance = node_factory.create(
                node_definition.node_type,
                node_definition.config
            )

            # 実行時に参照できるように definition を保持
            node_instance.definition = node_definition

            # Pipeline に追加
            node_instances.append(node_instance)

            # --------------------------------------------------------
            # 5. 入力アーティファクトの静的検証
            # --------------------------------------------------------
            # このノードが必要とする入力が、
            # ・すでに生成されているか
            # ・または外部から渡されているか
            # をチェックする
            pipeline._validate_node_inputs_static(
                node_instance,
                produced_artifacts,
                initial_artifacts
            )

            # --------------------------------------------------------
            # 6. 出力アーティファクトを記録
            # --------------------------------------------------------
            # このノードが生成する出力を記録することで、
            # 後続ノードの入力チェックに使う
            #
            # 例：
            #   NodeA が "text" を出力
            #   → NodeB が "text" を入力として使える
            output_keys = pipeline._get_node_output_keys(node_instance)

            for output_name in output_keys:
                produced_artifacts[output_name] = True

        # ------------------------------------------------------------
        # 7. Pipeline にノードを設定
        # ------------------------------------------------------------
        pipeline.nodes = node_instances

        # 元の definition も保持しておく（ログやDB用）
        pipeline.definition = pipeline_definition

        # 完成した Pipeline を返す
        return pipeline

    def _build_dependency_map(self, node_definitions: List) -> Dict[str, List[str]]:
        """
        ノード定義一覧から「依存関係マップ（DAG）」を構築する。

        -----------------------------
        ■ このメソッドの目的
        -----------------------------
        Pipeline 内の各ノードが、

            「どのノードの結果を待ってから実行するべきか」

        を明確にするためのデータ構造を作る。

        -----------------------------
        ■ 依存関係マップとは？
        -----------------------------
        以下のような辞書（Dictionary）構造：

            {
                "nodeB": ["nodeA"],   # nodeB は nodeA の完了を待つ
                "nodeC": ["nodeB"],   # nodeC は nodeB の完了を待つ
                "nodeA": []           # nodeA は依存なし（最初に実行できる）
            }

        -----------------------------
        ■ なぜ必要か？
        -----------------------------
        Pipeline 実行時に：

            「このノードは今実行していいのか？」

        を判断するために使う。

        例:
            nodeB は nodeA に依存している
            → nodeA が終わるまで nodeB は実行してはいけない

        -----------------------------
        ■ 明示依存と暗黙依存
        -----------------------------

        ● 明示依存（ユーザーが指定）
            depends_on に書かれているもの

        ● 暗黙依存（自動補完）
            depends_on が空の場合：
                → 直前のノードに依存させる

        -----------------------------
        ■ なぜ暗黙依存を入れるのか？
        -----------------------------
        ユーザーが以下のように書いた場合：

            node1
            node2
            node3

        depends_on を書かないと：

            「全部並列実行される」

        しかし多くの場合は：

            「上から順に実行したい」

        → そのため自動で：

            node2 → node1 に依存
            node3 → node2 に依存

        を追加する

        -----------------------------
        ■ 注意点
        -----------------------------
        - 並列実行したい場合は depends_on を明示的に指定する必要がある
        - この設計は「デフォルトは直列」という思想

        -----------------------------
        ■ 引数
        -----------------------------
        Args:
            node_definitions (List):
                ノード定義オブジェクトのリスト
                各要素は以下の属性を持つ想定：
                    - node_id
                    - depends_on

        -----------------------------
        ■ 戻り値
        -----------------------------
        Returns:
            Dict[str, List[str]]:
                node_id → 依存ノードID一覧

        -----------------------------
        ■ 例
        -----------------------------
        入力:

            node_definitions = [
                nodeA(depends_on=[]),
                nodeB(depends_on=[]),
                nodeC(depends_on=["nodeA"])
            ]

        出力:

            {
                "nodeA": [],
                "nodeB": ["nodeA"],   # ← 暗黙依存
                "nodeC": ["nodeA"]    # ← 明示依存
            }
        """

        # -------------------------
        # 依存関係マップ初期化
        # -------------------------
        dependency_map: Dict[str, List[str]] = {}

        # -------------------------
        # ① 明示的な依存関係をコピー
        # -------------------------
        # 各ノードの depends_on をそのままコピーする
        for node_definition in node_definitions:
            node_id = node_definition.node_id

            # depends_on が存在しない場合もあるため getattr を使用
            explicit_dependencies = list(
                getattr(node_definition, "depends_on", [])
            )

            dependency_map[node_id] = explicit_dependencies

        # -------------------------
        # ② 暗黙的な依存関係を補完
        # -------------------------
        # depends_on が空のノードについては、
        # 「直前のノード」に依存させることで直列実行を保証する
        for index, node_definition in enumerate(node_definitions):

            current_node_id = node_definition.node_id

            # 先頭ノードは依存を持てない（前がない）
            if index == 0:
                continue

            # すでに明示的な依存がある場合は何もしない
            if dependency_map[current_node_id]:
                continue

            # 直前のノードIDを取得
            previous_node_definition = node_definitions[index - 1]
            previous_node_id = previous_node_definition.node_id

            # 暗黙依存を追加
            dependency_map[current_node_id].append(previous_node_id)

        # -------------------------
        # 完成した依存関係マップを返す
        # -------------------------
        return dependency_map

    def _topological_sort(self, dependency_map: Dict[str, List[str]]) -> List[str]:
        """
        ノードの依存関係（DAG: 有向非循環グラフ）をもとに、
        「正しい実行順序」を決定する（トポロジカルソート）。

        -----------------------------
        ■ トポロジカルソートとは？
        -----------------------------
        「依存関係を壊さない順序に並び替えること」

        例:
            A → B → C

            （B は A に依存）
            （C は B に依存）

            → 実行順序は必ず:
                A → B → C

        -----------------------------
        ■ この関数の役割
        -----------------------------
        - Node の実行順序を決める
        - 依存ノードを必ず先に実行できるようにする
        - 循環依存（A→B→A）を検出する

        -----------------------------
        ■ 入力データの形式
        -----------------------------
        dependency_map:
            {
                "nodeB": ["nodeA"],   # B は A に依存
                "nodeC": ["nodeB"],   # C は B に依存
                "nodeA": []           # A は依存なし
            }

        -----------------------------
        ■ 出力
        -----------------------------
        ["nodeA", "nodeB", "nodeC"]

        -----------------------------
        ■ アルゴリズム概要（DFS）
        -----------------------------
        深さ優先探索（DFS）を使用する。

        ノードごとに以下を行う：

        1. 依存ノードを先に処理
        2. 自分自身を結果に追加

        -----------------------------
        ■ 循環依存の検出方法
        -----------------------------
        以下の2つの集合を使う：

        temp_mark_set:
            現在探索中のノード（再訪したら循環）

        perm_mark_set:
            完全に処理済みのノード

        例:
            A → B → A の場合

            Aを処理中にまたAに戻る
            → temp_mark に存在
            → 循環検出

        -----------------------------
        ■ 例外
        -----------------------------
        Raises:
            ValueError:
                循環依存が検出された場合
        """

        # -------------------------
        # 実行順序の結果リスト
        # -------------------------
        # 最終的にここに「正しい順序」で node_id が入る
        sorted_node_ids: List[str] = []

        # -------------------------
        # 一時マーク（探索中）
        # -------------------------
        # DFSの途中で訪れているノード
        # → ここに再度入ったら「循環」
        temporary_mark_set = set()

        # -------------------------
        # 永続マーク（処理済み）
        # -------------------------
        # 完全に処理が終わったノード
        # → ここにあるノードは再処理不要
        permanent_mark_set = set()

        def visit(current_node_id: str):
            """
            指定されたノードを DFS で訪問する内部関数。

            この関数は再帰的に呼ばれ、
            依存ノードをすべて先に処理する。

            Args:
                current_node_id (str):
                    現在処理しているノードID

            Raises:
                ValueError:
                    循環依存が検出された場合
            """

            # -------------------------
            # すでに処理済みなら何もしない
            # -------------------------
            if current_node_id in permanent_mark_set:
                return

            # -------------------------
            # 循環依存チェック
            # -------------------------
            # 「今まさに処理中のノード」に再度来たらループしている
            if current_node_id in temporary_mark_set:
                error_message = (
                    f"循環依存を検出しました: '{current_node_id}'\n"
                    f"ノード同士がループして依存しています。"
                )
                logger.error(error_message)
                raise ValueError(error_message)

            # -------------------------
            # 探索中としてマーク
            # -------------------------
            temporary_mark_set.add(current_node_id)

            # -------------------------
            # 依存ノードを先に処理
            # -------------------------
            # 例:
            #   A → B
            #   → B を先に visit する
            dependent_node_ids = dependency_map.get(current_node_id, [])

            for dependency_node_id in dependent_node_ids:
                visit(dependency_node_id)

            # -------------------------
            # 探索完了 → 一時マーク削除
            # -------------------------
            temporary_mark_set.remove(current_node_id)

            # -------------------------
            # 完全処理済みとして記録
            # -------------------------
            permanent_mark_set.add(current_node_id)

            # -------------------------
            # 結果リストに追加
            # -------------------------
            # 「依存ノードの後」に追加されるため、
            # 自然に正しい順序になる
            sorted_node_ids.append(current_node_id)

        # -------------------------
        # すべてのノードを対象に DFS 実行
        # -------------------------
        # dependency_map の順序をそのまま使う
        # （定義順を維持するため）
        for node_id in dependency_map:
            if node_id not in permanent_mark_set:
                visit(node_id)

        # -------------------------
        # 完成した実行順序を返す
        # -------------------------
        return sorted_node_ids

    def _get_node_input_keys(self, node):
        """
        Node の入力キー一覧を取得する。

        Args:
            node (Node): 対象ノード

        Returns:
            List[str]:
                入力キー一覧
        """
        if hasattr(node, 'inputs'):
            return list(node.inputs.keys()) if isinstance(node.inputs, dict) else list(node.inputs)
        return []

    def _get_node_output_keys(self, node):
        """
        Node の出力キー一覧を取得する。

        Args:
            node (Node): 対象ノード

        Returns:
            List[str]:
                出力キー一覧
        """
        if hasattr(node, 'outputs'):
            return list(node.outputs.keys()) if isinstance(node.outputs, dict) else list(node.outputs)
        return []

    def _validate_node_inputs_static(
        self,
        node_instance: Node,
        produced_output_artifacts: Dict[str, bool],
        initial_artifacts: Dict[str, str]
    ):
        """
        Node の入力アーティファクトを「実行前（静的）」に検証する。

        このメソッドは Pipeline 構築時（from_definition）に使用される。

        -----------------------------
        ■ なぜこの検証が必要か？
        -----------------------------
        Pipeline は「前のノードの出力」を「次のノードの入力」として使う。

        しかし、以下のような問題があると実行時にエラーになる：
        - 必要な入力が存在しない
        - 型が違う（例: text を期待しているのに image が来る）

        これを「実行前」に検出することで、
        実行時エラーを防ぎ、安全な Pipeline を構築できる。

        -----------------------------
        ■ 検証対象
        -----------------------------
        各 Node が要求する入力（node.inputs）について：

        ① initial_artifacts に含まれているか？
            → 外部入力として許可

        ② それ以外の場合：
            → 前のノードが出力済みか？

        -----------------------------
        ■ 引数
        -----------------------------
        Args:
            node_instance (Node):
                検証対象のノードインスタンス

            produced_output_artifacts (Dict[str, bool]):
                これまでに生成された出力アーティファクト一覧
                例:
                    {
                        "text": True,
                        "image": True
                    }

            initial_artifacts (Dict[str, str]):
                外部から与えられる初期アーティファクト
                例:
                    {
                        "prompt": "text"
                    }

        -----------------------------
        ■ 例
        -----------------------------
        Node.inputs = {"text": "string"}

        ケース1:
            produced_output_artifacts = {"text": True}
            → OK（前のノードが生成済み）

        ケース2:
            initial_artifacts = {"text": "string"}
            → OK（外部入力）

        ケース3:
            どちらにも存在しない
            → エラー（入力不足）

        -----------------------------
        ■ 例外
        -----------------------------
        Raises:
            ValueError:
                必要な入力が存在しない場合

            TypeError:
                初期アーティファクトの型が定義と一致しない場合
        """

        # -------------------------
        # Node が必要とする入力一覧を取得
        # -------------------------
        # 例:
        #   node.inputs = {"text": "string"}
        #   → ["text"]
        input_artifact_names = self._get_node_input_keys(node_instance)

        # -------------------------
        # 各入力について検証
        # -------------------------
        for input_name in input_artifact_names:

            # ==========================================
            # ① 外部入力（initial_artifacts）に存在するか？
            # ==========================================
            if initial_artifacts and input_name in initial_artifacts:

                # -------------------------
                # 型チェック（定義がある場合のみ）
                # -------------------------
                # node.inputs が dict の場合は型定義あり
                if isinstance(node_instance.inputs, dict):
                    expected_type = node_instance.inputs.get(input_name)
                else:
                    expected_type = None  # 型定義なし

                provided_type = initial_artifacts[input_name]

                # -------------------------
                # 型不一致チェック
                # -------------------------
                if expected_type and provided_type != expected_type:
                    error_message = (
                        f"初期アーティファクトの型不一致: '{input_name}'\n"
                        f"  期待される型: {expected_type}\n"
                        f"  実際の型: {provided_type}"
                    )
                    logger.error(error_message)
                    raise TypeError(error_message)

                # 外部入力が正しく提供されているので次へ
                continue

            # ==========================================
            # ② 前ノードの出力として存在するか？
            # ==========================================
            if input_name not in produced_output_artifacts:
                error_message = (
                    f"入力アーティファクトが未生成です: '{input_name}'\n"
                    f"ノード '{node_instance.definition.node_id}' の実行に必要ですが、"
                    f"前のノードから生成されていません。"
                )
                logger.error(error_message)
                raise ValueError(error_message)

            # -------------------------
            # OKケース
            # -------------------------
            # produced_output_artifacts に存在する場合は問題なし
            # → 次の入力へ

    def _compute_cache_key(self, node: Node, context: Context):
        """
        Node 実行結果をキャッシュするためのキー（識別子）を生成する。

        ------------------------------------------------------------
        ■ このメソッドの役割
        ------------------------------------------------------------
        同じ Node が「同じ入力・同じ設定」で実行される場合、
        再実行せずにキャッシュを使うために一意なキーを作成する。

        つまり：
            「この条件なら過去と同じ結果になるはず」
        という判断材料を作る処理。

        ------------------------------------------------------------
        ■ キャッシュキーに含める情報
        ------------------------------------------------------------
        キャッシュの正しさを担保するために、以下を含める：

        1. ノードの種類（node_type）
            → 処理の種類が違えば結果も変わるため

        2. 入力アーティファクト（artifact ID）
            → 入力データが違えば結果も変わるため

        3. ノード設定（config）
            → パラメータが違えば結果も変わるため

        ------------------------------------------------------------
        ■ なぜ artifact の「中身」ではなく「ID」なのか
        ------------------------------------------------------------
        - 実データを毎回ハッシュすると重い
        - Repository 側で ID によって内容が一意に管理されている前提

        ------------------------------------------------------------
        Args:
            node (Node):
                キャッシュ対象のノード

            context (Context):
                実行時コンテキスト（artifact の現在状態を保持）

        ------------------------------------------------------------
        Returns:
            Tuple:
                キャッシュキー（タプル形式）
                例:
                (
                    "text_generation",                   # ノードタイプ
                    (("input_text", "artifact_123"),),  # 入力
                    "abc123..."                         # config のハッシュ
                )
        """

        # ------------------------------------------------------------
        # 1. ノードタイプを取得
        # ------------------------------------------------------------
        # node.definition が存在する場合は node_type を使用
        # 無い場合はクラス名で代替
        node_type = getattr(
            node.definition,
            "node_type",
            node.__class__.__name__
        )

        # ------------------------------------------------------------
        # 2. 入力アーティファクト情報の収集
        # ------------------------------------------------------------
        # 入力として使用される artifact を収集する
        #
        # 例:
        #   {"input_text": "artifact_123"}
        #
        # ※ context.artifacts には
        #   「現在のアーティファクト名 → artifact ID」が入っている
        input_artifact_map = {}

        for input_name in self._get_node_input_keys(node):
            # context に存在する入力のみ対象にする
            if input_name in context.artifacts:
                input_artifact_map[input_name] = context.artifacts[input_name]

        # ------------------------------------------------------------
        # 3. ソートしてタプル化（順序を固定するため）
        # ------------------------------------------------------------
        # dict は順序保証が弱いため、
        # ソートしてから tuple に変換することで
        # 「順序による違い」を排除する
        #
        # 例:
        #   {"b":1, "a":2} → (("a",2), ("b",1))
        sorted_input_artifacts = tuple(
            sorted(input_artifact_map.items())
        )

        # ------------------------------------------------------------
        # 4. config のハッシュ化
        # ------------------------------------------------------------
        # config は dict のため、そのままだと比較しづらい
        # → JSON化してハッシュに変換する
        #
        # sort_keys=True によりキー順序を固定し、
        # 同じ内容なら同じ文字列になるようにする
        node_config = getattr(node.definition, "config", {})
        config_json = json.dumps(node_config, sort_keys=True)
        config_hash = hashlib.sha256(
            config_json.encode()
        ).hexdigest()

        # ------------------------------------------------------------
        # 5. キャッシュキーの生成
        # ------------------------------------------------------------
        # 上記3つを組み合わせて一意なキーを作る
        #
        # このキーが一致すれば：
        #   「同じ条件での実行」と判断できる
        cache_key = (
            node_type,
            sorted_input_artifacts,
            config_hash
        )

        return cache_key

    def run(
        self,
        context: Context,
        artifact_repository: ArtifactRepository,
        db_session=None
    ):
        """
        Pipeline を実行するメイン処理。

        ------------------------------------------------------------
        ■ このメソッドの役割
        ------------------------------------------------------------
        Pipeline に含まれる複数の Node を、
        「依存関係（DAG）」に従って正しい順序で実行する。

        また以下の責務も持つ：
            - 並列実行（依存関係がないノードは同時実行）
            - キャッシュ利用（同じ入力なら再実行しない）
            - 実行状態管理（DB連携）
            - エラーハンドリング

        ------------------------------------------------------------
        ■ 全体の流れ（重要）
        ------------------------------------------------------------
        1. PipelineRun を作成（DB連携がある場合）
        2. ノード依存関係（DAG）を構築
        3. 実行ループ開始
            - 実行可能なノードを探す
            - 並列で実行する
            - 完了したノードを回収する
        4. すべて完了したら終了

        ------------------------------------------------------------
        Args:
            context (Context):
                実行時の状態（アーティファクトの格納場所）

            artifact_repository (ArtifactRepository):
                アーティファクト保存・取得を行うリポジトリ

            db_session:
                DBセッション（指定時のみ実行履歴を保存）

        ------------------------------------------------------------
        Raises:
            RuntimeError:
                実行可能なノードが存在しない場合（循環依存の可能性）

            Exception:
                ノード実行時の例外
        """

        logger.info("[開始] パイプライン実行")

        # ------------------------------------------------------------
        # 1. PipelineRun（実行履歴）の作成
        # ------------------------------------------------------------
        pipeline_run_repository = None
        pipeline_run_record = None

        if db_session:
            from ai_helper.repository import PipelineRunRepository

            pipeline_run_repository = PipelineRunRepository(db_session)

            # PipelineDefinition からIDを取得
            pipeline_id = getattr(
                getattr(self, "definition", None),
                "id",
                ""
            ) or ""

            # 実行レコード作成
            pipeline_run_record = pipeline_run_repository.create(pipeline_id)

            # ステータスを「実行中」に更新
            pipeline_run_repository.update_status(
                pipeline_run_record.id,
                "RUNNING"
            )

        # ------------------------------------------------------------
        # 2. ノード間の依存関係（DAG）を構築
        # ------------------------------------------------------------
        # node.definition を使って dependency を構築
        dependency_map = self._build_dependency_map(
            [getattr(node, 'definition', node) for node in self.nodes]
        )

        logger.info(f"依存関係マップ: {dependency_map}")

        # ------------------------------------------------------------
        # 3. 実行状態の管理用変数
        # ------------------------------------------------------------

        # 現在実行中のノード
        # node_id -> Future
        running_nodes = {}

        # 実行完了したノードID
        completed_node_ids = set()

        # 並列実行時の排他制御用ロック
        execution_lock = threading.Lock()

        # ------------------------------------------------------------
        # 4. NodeExecutor の準備
        # ------------------------------------------------------------
        from ai_helper.core.executor import NodeExecutor

        node_executor = NodeExecutor(
            artifact_repository,
            db_session=db_session
        )

        # ------------------------------------------------------------
        # 5. ノード1件を実行する関数（スレッドから呼ばれる）
        # ------------------------------------------------------------
        def execute_single_node(target_node: Node):
            """
            単一ノードの実行処理。

            ThreadPoolExecutor から並列実行される。
            """

            node_id = getattr(
                target_node.definition,
                "node_id",
                target_node.__class__.__name__
            )

            # NodeExecutor に処理を委譲
            outputs = node_executor.execute(
                target_node,
                context,
                pipeline_run_id=(
                    pipeline_run_record.id
                    if pipeline_run_record else None
                )
            )

            # 完了登録（並列実行のためロック必須）
            with execution_lock:
                completed_node_ids.add(node_id)

            return outputs

        # ------------------------------------------------------------
        # 6. スレッドプール作成（並列実行用）
        # ------------------------------------------------------------
        thread_pool = ThreadPoolExecutor()

        # Future → Node の対応管理
        future_to_node_map = {}

        # ------------------------------------------------------------
        # 7. メイン実行ループ
        # ------------------------------------------------------------
        try:
            # 全ノードが完了するまでループ
            while len(completed_node_ids) < len(self.nodes):

                # ----------------------------------------------------
                # 7-1. 実行可能なノードを探す
                # ----------------------------------------------------
                for node in self.nodes:

                    node_id = getattr(node.definition, "node_id", None)

                    # すでに完了 or 実行中ならスキップ
                    if node_id in completed_node_ids or node_id in running_nodes:
                        continue

                    # ------------------------------------------------
                    # 依存関係チェック
                    # ------------------------------------------------
                    # 依存ノードがすべて完了しているか確認
                    dependencies = dependency_map.get(node_id, [])

                    if not all(dep_id in completed_node_ids for dep_id in dependencies):
                        # 依存未完了 → 実行不可
                        continue

                    # ------------------------------------------------
                    # キャッシュチェック
                    # ------------------------------------------------
                    cache_key = self._compute_cache_key(node, context)

                    if cache_key in self.cache:
                        # キャッシュヒット → 再実行しない
                        logger.info(f"ノード '{node_id}' はキャッシュヒット")

                        # キャッシュされた出力を復元
                        for artifact_name, artifact_id in self.cache[cache_key].items():
                            context.set_artifact(artifact_name, artifact_id)

                        # 完了扱いにする
                        completed_node_ids.add(node_id)
                        continue

                    # ------------------------------------------------
                    # 実行スケジューリング（並列実行）
                    # ------------------------------------------------
                    logger.info(f"ノード '{node_id}' を実行スケジュール")

                    future = thread_pool.submit(
                        execute_single_node,
                        node
                    )

                    future_to_node_map[future] = node
                    running_nodes[node_id] = future

                # ----------------------------------------------------
                # 7-2. デッドロック検出
                # ----------------------------------------------------
                # 実行中タスクが無いのに未完了ノードがある
                # → 循環依存の可能性
                if not future_to_node_map and len(completed_node_ids) < len(self.nodes):
                    raise RuntimeError("循環依存の可能性があります（実行不能状態）")

                # ----------------------------------------------------
                # 7-3. ノード完了待ち（1つ以上終わるまで待機）
                # ----------------------------------------------------
                done_futures, _ = wait(
                    future_to_node_map.keys(),
                    return_when=FIRST_COMPLETED
                )

                # ----------------------------------------------------
                # 7-4. 完了したノードの後処理
                # ----------------------------------------------------
                for completed_future in done_futures:
                    completed_node = future_to_node_map.pop(completed_future)
                    node_id = getattr(completed_node.definition, "node_id", None)

                    # 実行中リストから削除
                    running_nodes.pop(node_id, None)

                    # 実行結果取得（ここで例外も発生する）
                    outputs = completed_future.result()

                    # ------------------------------------------------
                    # キャッシュ保存
                    # ------------------------------------------------
                    cache_key = self._compute_cache_key(completed_node, context)

                    self.cache[cache_key] = outputs

        # ------------------------------------------------------------
        # 8. エラーハンドリング
        # ------------------------------------------------------------
        except Exception:

            # DB連携している場合は FAILED に更新
            if pipeline_run_repository:
                pipeline_run_repository.update_status(
                    pipeline_run_record.id,
                    "FAILED",
                    finished_at=datetime.datetime.now(datetime.UTC)
                )

            raise

        # ------------------------------------------------------------
        # 9. 終了処理
        # ------------------------------------------------------------
        finally:
            thread_pool.shutdown(wait=False)
            logger.info("[完了] パイプライン実行")