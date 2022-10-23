import logging
import os
import sys
import traceback
from typing import List, Optional

import numpy as np
from vosk_example_gui.audio import Audio
from vosk_example_gui.view import Event, Viwer
from vosk_example_gui.vosk_client import VoskClient


def get_path() -> str:
    """カレントディレクトリを返す（.exeの場合でも対応）

    Returns:
        str: カレントディレクトリのパス
    """
    base_dir = os.getcwd()
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    return base_dir


class App:
    def __init__(self) -> None:
        """Initialize"""
        self._logger = logging.getLogger("vosk_example_gui.app")
        self.word_list: List[str] = []

        # initialize instance
        self.audio = Audio()
        self.vosk = VoskClient()

        pulldown_list = []
        pulldown_default_idx = 0
        self.input_device_config, default_device_idx = self.audio.get_input_devices()
        for i, (dev_name, dev_id) in enumerate(self.input_device_config.items()):
            pulldown_list.append(dev_name)
            if dev_id == default_device_idx:
                pulldown_default_idx = i
        self._current_audio = pulldown_list[pulldown_default_idx]

        self.viewer = Viwer(
            word_list=self.word_list,
            pulldown_list=pulldown_list,
            pulldown_list_default_idx=pulldown_default_idx,
        )
        self.audio.start_streaming()
        self.vosk.initialize_model(
            self.word_list,
            self.audio.get_sampling_rate(),
            os.path.join(get_path(), "model"),
        )

    def run(self) -> None:
        """起動"""
        try:
            while True:
                event, content = self.viewer.get_event()
                audio_data = self.audio.get()
                # print(event, content)
                if event == Event.FINISH:
                    self._logger.info("close window.")
                    break
                if event == Event.ADD_WORD:
                    self.add_word(content)
                if event == Event.DELETE_WORD:
                    self.delete_word(content)
                if event == Event.SUBMIT_WORDS:
                    self.initialize_vosk()
                if event == Event.CHANGE_AUDIO:
                    self.change_audio_source(content)
                if event == Event.LOAD_FILE:
                    self.load_words_from_file(content)

                self.recognize(audio_data)
                self.update_waveform(audio_data)

        except Exception as e:
            self._logger.error(f"{e}")
            self._logger.error(f"{traceback.format_exc()}")
            pass
        except KeyboardInterrupt:
            pass
        finally:
            self._logger.info("close instance")
            self.viewer.close()
            self.audio.stop()

    def recognize(self, audio_data: Optional[bytes]) -> None:
        """voskによる音声認識を行い、認識結果をGUIに反映する。

        Args:
            audio_data (Optional[bytes]): マイクからの入力信号
        """
        if audio_data is None:
            return
        recognized = self.vosk.recognize(audio_data)
        if recognized is None:
            return
        self.viewer.update_text(recognized["result"])

    def add_word(self, word: str) -> None:
        """GUIで入力されたワードをword_listに追加する。（重複は弾く）

        Args:
            word (str): 入力ワード
        """
        if word not in self.word_list:
            self.word_list.append(word)
            self.viewer.update_table(self.word_list)

    def delete_word(self, target_word_idx_list: List) -> None:
        """GUIで選択されたワードをword_listから削除する。

        Args:
            target_word_idx_list (List): 削除対象のワードのインデックスリスト
        """
        for i in sorted(target_word_idx_list, reverse=True):
            self.word_list.pop(i)
        self.viewer.update_table(self.word_list)

    def change_audio_source(self, audio_source: str) -> None:
        """入力ソースを変更する。

        Args:
            audio_source (str): 変更したい入力ソース名
        """
        if self._current_audio == audio_source:
            return

        self._current_audio = audio_source
        self.audio.start_streaming(self.input_device_config[self._current_audio])

    def load_words_from_file(self, file_path: str) -> None:
        """ファイル内の単語をword_listに追加する。（重複は弾く）

        Args:
            file_path (str): 対象のファイルパス
        """
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
                for l in lines:
                    l = l.strip()
                    if l == "": continue
                    if l in self.word_list: continue
                    self.word_list.append(l)
            self.viewer.update_table(self.word_list)
        except IOError as e:
            self._logger.error(f"IO Error. {e}")
            self.viewer.show_error_popup(f"IO Error. {e}")
        except Exception as e:
            self._logger.error(f"{e}")
            self.viewer.show_error_popup(f"FILE Error. {e}")

    def update_waveform(self, audio_data: Optional[bytes]) -> None:
        """入力信号をGUI上のグラフに反映する。

        Args:
            audio_data (Optional[bytes]): マイクからの入力信号
        """
        if audio_data is None:
            return
        decode_wave = np.frombuffer(audio_data, dtype="int16") / 32767.0
        self.viewer.update_waveform(decode_wave)

    def initialize_vosk(self) -> None:
        """vosk_clientを初期化する。"""
        self.audio.stop()
        self.vosk.initialize_model(
            self.word_list,
            self.audio.get_sampling_rate(),
            os.path.join(get_path(), "model"),
        )
        self.audio.start()

    def _initialize_instance(self) -> None:
        """利用インスタンスを初期化する。"""
        self.audio = Audio()
        self.vosk = VoskClient()

        pulldown_list = []
        pulldown_default_idx = 0
        self.input_device_config, default_device_idx = self.audio.get_input_devices()
        for i, (dev_name, dev_id) in enumerate(self.input_device_config.items()):
            pulldown_list.append(dev_name)
            if dev_id == default_device_idx:
                pulldown_default_idx = i
        self._current_audio = pulldown_list[pulldown_default_idx]

        self.viewer = Viwer(
            word_list=self.word_list,
            pulldown_list=pulldown_list,
            pulldown_list_default_idx=pulldown_default_idx,
        )
        self.audio.start_streaming()
        self.vosk.initialize_model(
            self.word_list,
            self.audio.get_sampling_rate(),
            os.path.join(get_path(), "model"),
        )
