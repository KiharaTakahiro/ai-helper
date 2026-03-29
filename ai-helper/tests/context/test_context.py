def test_set_and_get_artifact(context):
    """
    観点:
        Contextがアーティファクトを正しく保存・取得できること
    """
    context.set_artifact("a", "123")

    assert context.get_artifact("a") == "123"


def test_get_missing_artifact_raises(context):
    """
    観点:
        存在しないキーを取得した場合にKeyErrorが発生すること
    """
    import pytest

    with pytest.raises(KeyError):
        context.get_artifact("missing")