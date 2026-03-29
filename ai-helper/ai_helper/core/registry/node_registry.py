from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Dict, List, Optional, Type

from ai_helper.core.node.base_node import BaseNode


class NodeRegistry:
    """
    Node（処理単位）のクラスを「自動発見・登録・検索」するためのレジストリクラス。

    -----------------------------
    ■ このクラスの役割
    -----------------------------
    このクラスは以下の責務を持つ：

    1. 指定されたパッケージ配下をスキャンする
    2. BaseNode を継承したクラスを探す
    3. 見つけたクラスを自動登録する
    4. 名前やタグでノードを検索できるようにする

    -----------------------------
    ■ 何が嬉しいのか？
    -----------------------------
    通常はノードを追加するたびに登録コードを書く必要があるが、
    この仕組みにより：

        「nodes/ にファイルを置くだけで使える」

    というプラグイン的な構造を実現できる。

    -----------------------------
    ■ 内部データ構造
    -----------------------------
    _nodes_by_name:
        ノード名 → ノードクラス

    _nodes_by_tag:
        タグ → ノードクラスのリスト
    """

    def __init__(
        self,
        nodes_package: str = "ai_helper.nodes",
        extra_packages: Optional[List[str]] = None
    ):
        """
        NodeRegistry を初期化する。

        -----------------------------
        ■ Args
        -----------------------------
        nodes_package (str):
            メインとなるノード探索対象パッケージ
            例: "ai_helper.nodes"

        extra_packages (List[str] | None):
            追加で探索したいパッケージ一覧
            プラグイン用途などで使用する

        -----------------------------
        ■ 処理内容
        -----------------------------
        1. 内部辞書を初期化
        2. discover_nodes() を呼び出して即スキャン開始
        """

        # メインの探索対象パッケージ
        self.nodes_package = nodes_package

        # 追加探索対象（未指定なら空リスト）
        self.extra_packages = extra_packages or []

        # ノード名 → クラス
        self._nodes_by_name: Dict[str, Type[BaseNode]] = {}

        # タグ → クラス一覧
        self._nodes_by_tag: Dict[str, List[Type[BaseNode]]] = {}

        # 初期化時に自動スキャンを実行
        self.discover_nodes()

    def _convert_class_name_to_snake_case(self, class_name: str) -> str:
        """
        クラス名（CamelCase）を snake_case に変換する。

        -----------------------------
        ■ 例
        -----------------------------
        MyAwesomeNode → my_awesome_node

        -----------------------------
        ■ なぜ必要か？
        -----------------------------
        ノードに name 属性が無い場合に、
        クラス名から自動で識別名を生成するため
        """
        import re

        # 大文字の区切りで _ を挿入
        step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)

        # 小文字→大文字の境界にも _ を挿入
        snake_case_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1).lower()

        return snake_case_name

    def discover_nodes(self):
        """
        ノードクラスを自動発見し、すべて登録し直す。

        -----------------------------
        ■ 処理の流れ
        -----------------------------
        1. 既存の登録情報をクリア
        2. 探索対象パッケージをリスト化
        3. 各パッケージを import
        4. pkgutil で配下モジュールを再帰的に取得
        5. 各モジュール内のクラスを走査
        6. BaseNode 継承クラスのみ登録

        -----------------------------
        ■ 注意点
        -----------------------------
        - import に失敗したモジュールは無視する
        - BaseNode 自体は登録しない
        - 外部から import されたクラスは除外する
        """

        # 既存データをリセット（再スキャンのため）
        self._nodes_by_name.clear()
        self._nodes_by_tag.clear()

        # 探索対象パッケージ一覧を作成
        packages_to_scan = [self.nodes_package] + self.extra_packages

        for package_name in packages_to_scan:

            # -------------------------
            # パッケージ import
            # -------------------------
            try:
                package = importlib.import_module(package_name)
            except ImportError:
                # 存在しない場合はスキップ
                continue

            # パッケージでない場合はスキップ
            if not hasattr(package, "__path__"):
                continue

            # -------------------------
            # サブモジュール探索
            # -------------------------
            for _, module_name, _ in pkgutil.walk_packages(
                package.__path__,
                package.__name__ + "."
            ):
                try:
                    module = importlib.import_module(module_name)
                except Exception:
                    # モジュール読み込み失敗は無視
                    continue

                # -------------------------
                # クラス探索
                # -------------------------
                for attribute_name in dir(module):
                    attribute_value = getattr(module, attribute_name)

                    # クラスでないものは無視
                    if not inspect.isclass(attribute_value):
                        continue

                    # BaseNode 自体は除外
                    if attribute_value is BaseNode:
                        continue

                    # 同一パッケージ内で定義されたクラスのみ対象
                    if not getattr(attribute_value, "__module__", "").startswith(package_name):
                        continue

                    # BaseNode のサブクラスのみ登録
                    if issubclass(attribute_value, BaseNode):
                        self.register_node(attribute_value)

    def register_node(
        self,
        node_class: Type[BaseNode],
        name: Optional[str] = None
    ):
        """
        ノードクラスを手動で登録する。

        -----------------------------
        ■ Args
        -----------------------------
        node_class:
            登録対象のノードクラス

        name:
            登録時の名前（省略時は自動生成）

        -----------------------------
        ■ 処理内容
        -----------------------------
        1. name が指定されていれば上書き
        2. 無ければクラス名から生成
        3. 名前辞書へ登録
        4. タグ辞書へ登録
        """

        # 名前を明示指定した場合は上書き
        if name is not None:
            node_class.name = name

        # BaseNode 自体は登録しない
        if node_class is BaseNode:
            return

        # -------------------------
        # ノード名決定
        # -------------------------
        node_name = getattr(node_class, "name", None)

        if not node_name:
            # クラス名から自動生成
            node_name = self._convert_class_name_to_snake_case(node_class.__name__)
            node_class.name = node_name

        # -------------------------
        # 名前登録
        # -------------------------
        self._nodes_by_name[node_name] = node_class

        # -------------------------
        # タグ登録
        # -------------------------
        for tag in getattr(node_class, "tags", []) or []:
            if tag not in self._nodes_by_tag:
                self._nodes_by_tag[tag] = []

            self._nodes_by_tag[tag].append(node_class)

    def get_node_by_name(self, node_name: str) -> Type[BaseNode]:
        """
        ノード名からノードクラスを取得する。

        Raises:
            KeyError:
                指定された名前のノードが存在しない場合
        """
        return self._nodes_by_name[node_name]

    def get_nodes_by_tag(self, tag: str) -> List[Type[BaseNode]]:
        """
        指定したタグを持つノード一覧を取得する。
        """
        return list(self._nodes_by_tag.get(tag, []))

    def get_all_nodes(self) -> List[Type[BaseNode]]:
        """
        登録されている全ノードクラスを取得する。
        """
        return list(self._nodes_by_name.values())

    def unregister_node(self, node_name: str):
        """
        指定した名前のノード登録を解除する。

        -----------------------------
        ■ 処理内容
        -----------------------------
        1. 名前辞書から削除
        2. タグ辞書からも削除
        """

        node_class = self._nodes_by_name.pop(node_name, None)

        if node_class is None:
            return

        # タグ側からも削除
        for tag, node_class_list in list(self._nodes_by_tag.items()):
            self._nodes_by_tag[tag] = [
                cls for cls in node_class_list if cls is not node_class
            ]

            # 空になったタグは削除
            if not self._nodes_by_tag[tag]:
                del self._nodes_by_tag[tag]