from abc import ABC, abstractmethod
from typing import List
from ai_helper.pipeline.models import NodeDefinition

class BaseNode(ABC):
    """プラグイン対応のノード基底クラス。

    この抽象クラスは名前・タグ・入出力仕様を保持し、
    実際の処理は ``execute`` メソッドで定義される。
    サブクラスはクラス属性として ``name``/``tags`` を設定するか、
    コンストラクタ引数でオーバーライドすることができる。

    属性:
        name (str): ノードを識別する一意な名前。
        tags (List[str]): 検索やフィルタリングに利用するタグ。
        inputs (List[str] | Dict[str,str]): 期待する入力アーティファクト。
        outputs (List[str] | Dict[str,str]): 生成する出力アーティファクト。
        definition: 任意のノード定義情報（例: 入力/出力の詳細仕様など）。
    """

    # クラス属性によるデフォルト値
    name: str = ""
    tags: List[str] = []
    inputs: list = []
    outputs: list = []
    definition: NodeDefinition = None

    def __init__(self, name: str | None = None, tags: list[str] | None = None,
                 inputs: list | dict | None = None, outputs: list | dict | None = None):
        """インスタンス初期化。

        Args:
            name: インスタンス固有の名前（省略時はクラス属性を使用）。
            tags: タグ一覧（省略時はクラス属性を使用）。
            inputs: 入力アーティファクト仕様。
            outputs: 出力アーティファクト仕様。
        """
        if name is not None:
            self.name = name
        if tags is not None:
            self.tags = tags
        if inputs is not None:
            self.inputs = inputs
        if outputs is not None:
            self.outputs = outputs

    def __init_subclass__(cls, **kwargs):
        """
        サブクラスが定義されたタイミングで自動的に呼び出されるフック処理。

        ------------------------------------------------------------
        ■ __init_subclass__ とは？
        ------------------------------------------------------------
        Pythonでは「クラスが定義された瞬間」に実行される特別なメソッド。

        つまり：

            class MyNode(BaseNode):
                ...

        と書いた瞬間に、このメソッドが自動で実行される。

        ------------------------------------------------------------
        ■ このメソッドの目的
        ------------------------------------------------------------
        Nodeクラスの品質を強制的に担保すること。

        具体的には：

        1. name が未設定なら自動生成する
        2. tags の型が正しいかチェックする

        ------------------------------------------------------------
        ■ なぜここでやるのか？
        ------------------------------------------------------------
        インスタンス生成時では遅いから。

        クラス定義時にチェックすることで：

        - 不正なNodeを早期に検出できる
        - 実行時エラーを減らせる
        - 開発者のミスを防げる

        ------------------------------------------------------------
        ■ 例：自動 name 生成
        ------------------------------------------------------------
        クラス名:
            MyAwesomeNode

        自動変換:
            my_awesome_node

        → NodeRegistry などで扱いやすくなる

        ------------------------------------------------------------
        ■ Args
        ------------------------------------------------------------
        cls:
            定義されたサブクラス自身

        kwargs:
            クラス定義時に渡される追加引数（通常は未使用）
        """

        super().__init_subclass__(**kwargs)

        # ------------------------------------------------------------
        # ① name が未設定の場合は自動生成する
        # ------------------------------------------------------------
        if not getattr(cls, "name", None):
            import re

            # CamelCase → snake_case に変換
            step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
            snake_case_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1).lower()

            cls.name = snake_case_name

        # ------------------------------------------------------------
        # ② tags の型チェック
        # ------------------------------------------------------------
        if not isinstance(cls.tags, list):
            raise TypeError("tags は文字列のリストで指定する必要があります（例: ['nlp', 'image']）")

    def validate(self, context, runtime):
        """ノード実行前のバリデーション処理。

        デフォルトでは何もしないが、必要に応じてサブクラスでオーバーライドして
        入力アーティファクトの存在チェックや前提条件の検証を行うことができる。
        バリデーションに失敗した場合は例外を投げるべきである。

        Args:
            context: 実行コンテキストオブジェクト。
            runtime: ランタイムやリポジトリ等の環境オブジェクト。
        """
        pass

    @abstractmethod
    def execute(self, context, runtime):
        """ノードのメイン処理を記述する。

        このメソッドは必ずオーバーライドされるべきであり、
        パイプライン実行時に各ノードごとに呼び出される。
        ``runtime`` には通常 ``ArtifactRepository`` や外部ランタイム
        オブジェクトが渡される。

        戻り値としては、出力アーティファクト名からアーティファクトIDへの
        マッピングを返すことが期待されるが、旧来の ``run``
        インターフェースを使用する場合には ``None`` を返してもよい。

        Args:
            context: 実行コンテキストオブジェクト。
            runtime: ランタイムやリポジトリ等の環境オブジェクト。
        """
        pass
