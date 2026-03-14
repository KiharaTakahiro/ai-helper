"""Core artifact subpackage."""

from .types import ArtifactType

# 実装は infra/storage に移動したためここではインターフェースのみ提供
__all__ = ["ArtifactRepository", "ArtifactType"]
