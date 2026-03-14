"""
アーティファクト関連のコアモジュール。

パイプライン内で生成されるデータ（Artifact）の
型定義やインターフェースを提供する。

実際の保存処理は infra/storage 層で実装される。
"""
from .types import ArtifactType

# 実装は infra/storage に移動したためここではインターフェースのみ提供
__all__ = ["ArtifactRepository", "ArtifactType"]
