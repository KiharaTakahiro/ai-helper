NODE_REGISTRY = {}


# plugin loading is done at import time to register nodes automatically

def _load_plugins():
    try:
        import pkgutil
        import importlib
        import ai_helper.plugins as plugins_pkg
    except ImportError:
        return
    # iterate submodules/packages
    for finder, name, ispkg in pkgutil.iter_modules(plugins_pkg.__path__):
        try:
            importlib.import_module(f"{plugins_pkg.__name__}.{name}")
        except Exception:
            # plugin errors should not prevent engine startup
            pass


def _scan_node_packages():
    """`ai_helper.nodes` 配下を走査し、Node サブクラスを自動登録する。

    各モジュールをインポートし、その中の ``Node`` 派生クラスを探す。
    クラス名をスネークケースに変換して登録名とする。
    """
    try:
        import pkgutil
        import importlib
        import inspect
        from ai_helper.core.node import Node
        import ai_helper.nodes as nodes_pkg
    except ImportError:
        return

    def _snake_case(name: str) -> str:
        import re
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    for finder, modname, ispkg in pkgutil.walk_packages(nodes_pkg.__path__, nodes_pkg.__name__ + "."):
        try:
            module = importlib.import_module(modname)
        except Exception:
            continue
        for attr in dir(module):
            obj = getattr(module, attr)
            if inspect.isclass(obj) and issubclass(obj, Node) and obj is not Node:
                name = _snake_case(attr)
                # avoid overwriting an existing registration
                if name not in NODE_REGISTRY:
                    NODE_REGISTRY[name] = obj

# call loader once
_load_plugins()
# after plugins, scan the built-in nodes directory
_scan_node_packages()


# call loader once
_load_plugins()


def register_node(name: str, node_cls):
    """ノードクラスを名前付きで登録する。

    名前重複時は上書きしないように検査可能だが、現状は単純登録。
    """
    NODE_REGISTRY[name] = node_cls


def get_node_class(name: str):
    """登録済みノード名からクラスを取り出す。

    Args:
        name (str): 登録時に使用した文字列。

    Returns:
        クラスオブジェクト。
    """
    return NODE_REGISTRY[name]


# --- plugin loading -------------------------------------------------
# 類似したパッケージ (ai_helper.plugins) 下のモジュールを動的に
# インポートし、各プラグイン内部で register_node() が実行される
# ことを期待する。これにより外部提供ノードの自動検出が可能。
import pkgutil
import importlib

try:
    import ai_helper.plugins as _plugins_pkg
except ImportError:
    _plugins_pkg = None

if _plugins_pkg is not None:
    for finder, name, ispkg in pkgutil.iter_modules(_plugins_pkg.__path__, _plugins_pkg.__name__ + "."):
        try:
            importlib.import_module(name)
        except Exception:
            # loading failure should not break registry initialization
            pass
