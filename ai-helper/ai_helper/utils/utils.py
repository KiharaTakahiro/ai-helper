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