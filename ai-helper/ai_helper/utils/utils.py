import media_utils

import logging
logger = logging.getLogger(__name__)

def load_yml(path: str) -> dict:
    """
      YML ファイルを読み込むユーティリティ関数。

      Args:
          path (str): YML ファイルのパス。

      Returns:
          dict: 読み込まれた YML ファイルの内容。
    """

    if path.endswith('.yml') or path.endswith('.yaml'):
        logger.error("ファイルパスが.ymlまたは.yamlで終わっていません。")
        raise ValueError("YML ファイルの拡張子は .yml または .yaml でなければなりません。")

    try: 
      import yaml
      with open(path, 'r') as file:
          return yaml.safe_load(file)
    except ImportError:
      logger.error("PyYAML がインストールされていません。'pip install pyyaml' でインストールしてください。")
      raise
    except Exception as e:
      logger.error(f"YML ファイルの読み込みに失敗しました: {e}")
      raise

def create_yml(path: str, data: dict):
    """
        YMLファイルを作成する

        Args:
            path (str): ymlファイルの出力パス
            data (dict): ymlファイルの内容
    """
    if not (path.endswith('.yml') or path.endswith('.yaml')):
        logger.error("ファイルパスが.ymlまたは.yamlで終わっていません。")
        raise ValueError("YML ファイルの拡張子は .yml または .yaml でなければなりません。")

    try:
        import yaml
        with open(path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
    except ImportError:
        logger.error("PyYAML がインストールされていません。'pip install pyyaml' でインストールしてください。")
        raise
    except Exception as e:
        logger.error(f"YML ファイルの作成に失敗しました: {e}")
        raise

def load_json(path) -> dict:
    """
      JSON ファイルを読み込むユーティリティ関数。

      Args:
          path (str): JSON ファイルのパス。

      Returns:
          dict: 読み込まれた JSON ファイルの内容。
    """
    import json
    if path.endswith('.json'):
      logger.error("ファイルパスが.jsonで終わっていません。")
      raise ValueError("JSON ファイルの拡張子は .json でなければなりません。")
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"JSON ファイルの読み込みに失敗しました: {e}")
        raise

def create_json(path, data):
    """
        JSONファイルを作成する

        Args:
            path (str): JSONファイルの出力パス
            data (dict): JSONファイルの内容
    """
    import json
    if not path.endswith('.json'):
        logger.error("ファイルパスが.jsonで終わっていません。")
        raise ValueError("JSON ファイルの拡張子は .json でなければなりません。")
    try:
        with open(path, 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON ファイルの作成に失敗しました: {e}")
        raise
    
def extract(input_path, output_path, **kwargs):
    """
    動画ファイルから音声を抽出する。

    Args:
        input_path (str): 入力動画ファイル
        output_path (str): 出力音声ファイル

    Returns:
        dict: 実行結果
    """
    return media_utils.extract(input_path, output_path, **kwargs)

def convert(input_path, output_path, **kwargs):
    """
    音声フォーマットを変換する。

    Args:
        input_path (str): 入力音声ファイル
        output_path (str): 出力音声ファイル

    Returns:
        dict: 実行結果
    """
    return media_utils.convert(input_path, output_path, **kwargs)

def volume(input_path, output_path, level=1.0, **kwargs):
    """
    音量を調整する。

    Args:
        input_path (str): 入力音声ファイル
        output_path (str): 出力音声ファイル
        level (float): 音量倍率（1.0が基準）

    Returns:
        dict: 実行結果
    """
    return media_utils.volume(input_path, output_path, level=level, **kwargs)

def remove_silence(input_path, output_path, **kwargs):
    """
    音声から無音部分を削除する。

    Args:
        input_path (str): 入力音声ファイル
        output_path (str): 出力音声ファイル

    Returns:
        dict: 実行結果
    """
    return media_utils.remove_silence(input_path, output_path, **kwargs)

def normalize(input_path, output_path):
    """
    音声を正規化する（音量を均一化する）。

    ※この機能はpydubライブラリが必要。

    Args:
        input_path (str): 入力音声ファイル
        output_path (str): 出力音声ファイル

    Returns:
        None
    """
    media_utils.normalize(input_path, output_path)

def batch_convert(files, out_ext="mp4"):
    """
    複数ファイルを一括で変換する。

    Args:
        files (list[str]): 入力ファイルのリスト
        out_ext (str): 出力拡張子（例: mp4, mp3）

    Returns:
        list[dict]: 各ファイルの処理結果
    """
    return media_utils.batch_convert(files, out_ext=out_ext)

def resize(input_path, output_path, width=None, height=None):
    """
    画像のサイズを変更する。

    Args:
        input_path (str): 入力画像ファイル
        output_path (str): 出力画像ファイル
        width (int, optional): 出力幅
        height (int, optional): 出力高さ

    Returns:
        None
    """
    media_utils.resize(input_path, output_path, width=width, height=height)

def crop(input_path, output_path, x, y, width, height):
    """
    画像を指定領域でクロップする。

    Args:
        input_path (str): 入力画像
        output_path (str): 出力画像
        x (int): 左上X座標
        y (int): 左上Y座標
        width (int): 幅
        height (int): 高さ

    Returns:
        None
    """
    media_utils.crop(input_path, output_path, x, y, width, height)

def rotate(input_path, output_path, angle):
    """
    画像を回転する。

    Args:
        input_path (str): 入力画像
        output_path (str): 出力画像
        angle (float): 回転角度（度）

    Returns:
        None
    """
    media_utils.rotate(input_path, output_path, angle)

def draw_text(input_path, output_path, text):
    """
    画像にテキストを描画する。

    Args:
        input_path (str): 入力画像
        output_path (str): 出力画像
        text (str): 描画する文字列

    Returns:
        None
    """
    media_utils.draw_text(input_path, output_path, text)

def get_duration(path):
    """
    メディアファイルの再生時間（秒）を取得する。

    Args:
        path (str): 対象ファイルパス

    Returns:
        float: 再生時間（秒）
    """
    return media_utils.get_duration(path)

def get_info(path):
    """
    メディアファイルの詳細情報を取得する。

    pymediainfoがインストールされている場合は詳細情報を返す。

    Args:
        path (str): 対象ファイルパス

    Returns:
        dict: メディア情報
    """
    return media_utils.get_info(path)

def trim(input_path, output_path, start, duration, **kwargs):
    """
    動画の指定区間を切り出す。

    Args:
        input_path (str): 入力動画ファイルパス
        output_path (str): 出力ファイルパス
        start (float): 開始時間（秒）
        duration (float): 切り出す長さ（秒）

    Returns:
        dict: 実行結果
    """
    return media_utils.trim(input_path, output_path, start, duration, **kwargs)

def concat(inputs, output_path, **kwargs):
    """
    複数の動画ファイルを結合する。

    Args:
        inputs (list[str]): 入力ファイルのリスト
        output_path (str): 出力ファイルパス

    Returns:
        dict: 実行結果
    """
    return media_utils.concat(inputs, output_path, **kwargs)

def resize(input_path, output_path, width=None, height=None, **kwargs):
    """
    動画のサイズを変更する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力動画
        width (int, optional): 幅
        height (int, optional): 高さ

    Returns:
        dict: 実行結果
    """
    return media_utils.resize(input_path, output_path, width=width, height=height, **kwargs)

def crop(input_path, output_path, x, y, width, height, **kwargs):
    """
    動画を指定領域でクロップする。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力動画
        x (int): 左上X座標
        y (int): 左上Y座標
        width (int): 幅
        height (int): 高さ

    Returns:
        dict: 実行結果
    """
    return media_utils.crop(input_path, output_path, x, y, width, height, **kwargs)

def rotate(input_path, output_path, angle=90, **kwargs):
    """
    動画を回転する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力動画
        angle (int): 回転角度（90/180/270）

    Returns:
        dict: 実行結果
    """
    return media_utils.rotate(input_path, output_path, angle=angle, **kwargs)

def thumbnail(input_path, output_path, time=1, **kwargs):
    """
    指定時刻のフレームからサムネイル画像を生成する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力画像
        time (float): 抽出する時間（秒）

    Returns:
        dict: 実行結果
    """
    return media_utils.thumbnail(input_path, output_path, time=time, **kwargs)

def to_gif(input_path, output_path, **kwargs):
    """
    動画をGIF形式に変換する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力GIF

    Returns:
        dict: 実行結果
    """
    return media_utils.to_gif(input_path, output_path, **kwargs)

def reverse(input_path, output_path, **kwargs):
    """
    動画を逆再生する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力動画

    Returns:
        dict: 実行結果
    """
    return media_utils.reverse(input_path, output_path, **kwargs)

def speed(input_path, output_path, speed=2.0, **kwargs):
    """
    動画の再生速度を変更する。

    Args:
        input_path (str): 入力動画
        output_path (str): 出力動画
        speed (float): 再生速度倍率

    Returns:
        dict: 実行結果
    """
    return media_utils.speed(input_path, output_path, speed=speed, **kwargs)

def merge_audio_video(video_path, audio_path, output_path, **kwargs):
    """
    動画と音声を結合する。

    Args:
        video_path (str): 動画ファイル
        audio_path (str): 音声ファイル
        output_path (str): 出力ファイル

    Returns:
        dict: 実行結果
    """
    media_utils.merge_audio_video(video_path, audio_path, output_path, **kwargs)

def extract_frames(input_path, output_dir, **kwargs):
    """
    動画からフレームを連番画像として抽出する。

    Args:
        input_path (str): 入力動画
        output_dir (str): 出力ディレクトリ

    Returns:
        dict: 実行結果
    """
    return media_utils.extract_frames(input_path, output_dir, **kwargs)