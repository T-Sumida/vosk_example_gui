import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

from vosk_example_gui.app import App

root = logging.getLogger(__name__)


def get_current_dir_path() -> str:
    """ファイルの存在するカレントディレクトリのパスを取得する。
    Returns:
        str: カレントディレクトリの絶対パス
    """
    dir_path = "."
    if getattr(sys, "frozen", False):
        dir_path = os.path.dirname(sys.executable)
    elif __file__:
        dir_path = os.getcwd()
    return dir_path


def setup_log() -> None:
    """ログ出力の設定"""
    LOG_LEVEL = logging.INFO

    # ストリームハンドラの設定 コンソール出力が必要な場合に設定
    stream_handler = logging.StreamHandler()
    # ログレベルの設定
    stream_handler.setLevel(LOG_LEVEL)
    # ログ出力フォーマットを設定
    stream_handler.setFormatter(
        logging.Formatter("[{asctime}] {name:<8s} {levelname:<8s} {message}", style="{")
    )

    # ローテーションのタイミングを100キロバイト
    max_bytes = 10000 * 1024
    # 保持する旧ファイル数
    backup_count = 1
    file_handler = RotatingFileHandler(
        os.path.join(get_current_dir_path(), "vosk_example_gui_sys.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    # ログレベルの設定
    stream_handler.setLevel(LOG_LEVEL)
    # ログ出力フォーマットを設定
    file_handler.setFormatter(
        logging.Formatter("[{asctime}] {name:<8s} {levelname:<8s} {message}", style="{")
    )

    # ルートロガーの設定
    logging.basicConfig(level=LOG_LEVEL, handlers=[stream_handler, file_handler])


def main() -> None:
    try:
        app = App()
        root.info("app start")
        app.run()
    except Exception as e:
        root.error(f"{e}")
        root.error(f"{traceback.format_exc()}")


if __name__ == "__main__":
    setup_log()
    main()
