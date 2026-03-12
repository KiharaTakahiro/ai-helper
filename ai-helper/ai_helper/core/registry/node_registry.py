from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from ai_helper.core.node.base_node import BaseNode


class NodeRegistry:
    """ノードクラスの発見・保持を行うレジストリ。

    ディレクトリやパッケージをスキャンして ``BaseNode`` 派生クラスを
    自動登録し、名前やタグで検索できるようにする。プラグイン機能の
    基盤としても機能する。
    """

    def __init__(self, nodes_package: str = "ai_helper.nodes", extra_packages: Optional[List[str]] = None):
        """初期化。

        Args:
            nodes_package (str): デフォルトでスキャンするノード用パッケージ名。
            extra_packages (List[str] | None): 追加でスキャンしたいパッケージ名。
        """
        self.nodes_package = nodes_package
        self.extra_packages = extra_packages or []
        self._by_name: Dict[str, Type[BaseNode]] = {}
        self._by_tag: Dict[str, List[Type[BaseNode]]] = {}
        # 初回スキャン
        self.discover_nodes()

    def _snake_case(self, name: str) -> str:
        import re

        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def discover_nodes(self):
        """登録済みノードをクリアし、設定パッケージ一覧を再スキャンする。"""
        self._by_name.clear()
        self._by_tag.clear()

        packages = [self.nodes_package] + self.extra_packages
        for pkg_name in packages:
            try:
                pkg = importlib.import_module(pkg_name)
            except ImportError:
                continue
            if not hasattr(pkg, "__path__"):
                continue
            for finder, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                try:
                    module = importlib.import_module(modname)
                except Exception:
                    # モジュール読み込み失敗は無視
                    continue
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if inspect.isclass(obj) and issubclass(obj, BaseNode) and obj is not BaseNode:
                        self.register_node(obj)

    def register_node(self, node_class: Type[BaseNode], name: Optional[str] = None):
        """ノードクラスを手動で登録する。

        Args:
            node_class (Type[BaseNode]): 登録対象のクラス。
            name (str | None): 登録時に使う名前。省略時は ``node_class.name`` を利用。
        """
        if name is not None:
            node_class.name = name
        key = getattr(node_class, "name", None)
        if not key:
            # class name から自動生成
            key = self._snake_case(node_class.__name__)
            node_class.name = key
        self._by_name[key] = node_class
        # タグ登録
        for tag in getattr(node_class, "tags", []) or []:
            self._by_tag.setdefault(tag, []).append(node_class)

    def get_node_by_name(self, name: str) -> Type[BaseNode]:
        """名前でノードクラスを取得する。

        Raises:
            KeyError: 該当するノードが存在しない場合。
        """
        return self._by_name[name]

    def get_nodes_by_tag(self, tag: str) -> List[Type[BaseNode]]:
        """タグに紐づくノードクラスのリストを返す。"""
        return list(self._by_tag.get(tag, []))

    def all_nodes(self) -> List[Type[BaseNode]]:
        """登録されている全ノードクラスを取得する。"""
        return list(self._by_name.values())

    def unregister_node(self, name: str):
        """名前を指定してノード登録を解除する。"""
        cls = self._by_name.pop(name, None)
        if cls is None:
            return
        # タグ辞書からも削除
        for tag, lst in list(self._by_tag.items()):
            self._by_tag[tag] = [c for c in lst if c is not cls]
            if not self._by_tag[tag]:
                del self._by_tag[tag]
