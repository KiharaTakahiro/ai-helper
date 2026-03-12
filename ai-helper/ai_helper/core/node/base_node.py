from abc import ABC, abstractmethod
from typing import List


class BaseNode(ABC):
    """プラグイン対応のノード基底クラス。

    各ノードはこのクラスを継承し、`name` および `tags` をクラス属性で
   定義し、`execute` メソッドを実装する。

    属性:
        name (str): ノードを識別する一意の名前。クラス名から自動生成される
            が、明示的に指定することもできる。
        tags (List[str]): 検索やフィルタリングに利用する複数のタグ。
    """

    # 実際のサブクラスでオーバーライドされる
    name: str = ""
    tags: List[str] = []

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

        Args:
            context: 実行コンテキストオブジェクト。
            runtime: ランタイムやリポジトリ等の環境オブジェクト。
        """
        pass
