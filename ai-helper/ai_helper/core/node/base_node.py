from abc import ABC, abstractmethod
from typing import List


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
    """

    # クラス属性によるデフォルト値
    name: str = ""
    tags: List[str] = []
    inputs: list = []
    outputs: list = []

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
        """サブクラス作成時に基本的な検証を行う。"""
        super().__init_subclass__(**kwargs)
        # name が未設定ならクラス名を snake_case に変換して設定
        if not getattr(cls, "name", None):
            # simple snake case conversion
            import re

            s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
            snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
            cls.name = snake
        # ensure tags is a list
        if not isinstance(cls.tags, list):
            raise TypeError("tags must be a list of strings")

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
