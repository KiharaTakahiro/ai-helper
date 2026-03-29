def test_artifact_repository_save_and_load(artifact_repository):
    """
    観点:
        保存したデータが同一内容で取得できること
    """
    artifact_repository.save("a", "data")

    assert artifact_repository.load("a") == "data"


def test_artifact_repository_delete(artifact_repository):
    """
    観点:
        削除後にデータが取得できないこと
    """
    import pytest

    artifact_repository.save("a", "data")
    artifact_repository.delete("a")

    with pytest.raises(KeyError):
        artifact_repository.load("a")