import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_directory='./logs', log_file_name='ai_helper.log', log_level=logging.INFO, log_rotation_when='midnight', log_rotation_term=1, log_backup_count=7):
    """ロギングの設定を行う関数"""
    # ログのディレクトリが存在しない場合は作成
    log_directory.mkdir(exist_ok=True)

    # ログのフォーマットを定義
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    # ルートロガーの設定
    root = logging.getLogger()
    root.setLevel(log_level)

    # コンソール
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # 日次ローテーションログ
    file_handler = TimedRotatingFileHandler(
        log_directory / log_file_name,
        when=log_rotation_when,
        interval=log_rotation_term,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    
    # ログファイルのローテーション後に新しいファイルに切り替えるための設定
    file_handler.setFormatter(formatter)

    # ルートロガーにハンドラーを追加
    root.addHandler(console)
    root.addHandler(file_handler)