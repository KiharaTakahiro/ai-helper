import pytest
from ai_helper.core.context import Context
from ai_helper.core.storage.memory import MemoryStorage
from ai_helper.core.repository.artifact_repository import ArtifactRepository


@pytest.fixture
def context():
    """テスト用の空コンテキストを提供する"""
    return Context()


@pytest.fixture
def artifact_repository():
    """インメモリストレージを使用したArtifactRepository"""
    return ArtifactRepository(MemoryStorage())