import tempfile
from ai_helper.core.storage.file import FileStorage


def test_file_storage_save_and_load():
    """
    観点:
        ファイルとしてデータが保存され、正しく読み出せること
    """
    with tempfile.TemporaryDirectory() as tmp:
        storage = FileStorage(tmp)

        storage.save("a.txt", "hello")

        data = storage.load(f"{tmp}/a.txt")

        assert data == b"hello"


def test_file_storage_delete():
    """
    観点:
        ファイル削除が正しく行われること
    """
    with tempfile.TemporaryDirectory() as tmp:
        storage = FileStorage(tmp)

        storage.save("a.txt", "hello")

        storage.delete(f"{tmp}/a.txt")

        assert storage.exists("a.txt") is False