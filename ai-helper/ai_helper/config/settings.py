# プロジェクト設定用プレースホルダ

class Settings:
    """アプリケーション設定をまとめるクラス。"""

    def __init__(self):
        # デバッグモードのオン/オフ
        self.debug = True
        # アーティファクト保存ディレクトリのベース
        self.base_artifact_dir = "workspace"


def get_settings():
    """設定インスタンスを返すヘルパー"""
    return Settings()
