from ai_helper.core.storage.memory import MemoryStorage


def test_memory_storage_crud():
    """
    観点:
        メモリストレージがCRUD操作を正しく行えること
    """
    storage = MemoryStorage()

    storage.save("a", "data")

    assert storage.load("a") == "data"
    assert storage.exists("a") is True

    storage.delete("a")

    assert storage.exists("a") is False