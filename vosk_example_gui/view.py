import logging
from enum import Enum
from typing import Any, List, Optional, Tuple

import numpy as np
import PySimpleGUI as sg
from vosk_example_gui.config import GUI_APP_NAME


class Event(Enum):
    NONE: int = 0
    FINISH: int = 1
    ADD_WORD: int = 2
    DELETE_WORD: int = 3
    SUBMIT_WORDS: int = 4
    CHANGE_AUDIO: int = 5
    LOAD_FILE: int = 6


class _GUI_KEY:
    TABLE_KEY: str = "__TABLE__"
    ADD_BUTTON_KEY: str = "__ADD__"
    FILE_PATH_KEY: str = "__FILE_PATH__"
    FILE_LOAD_BUTTON_KEY: str = "__FILE__"
    SUBMIT_BUTTON_KEY: str = "__SUBMIT__"
    INPUT_TEXT_KEY: str = "__WORD_TEXT__"
    WAVEFORM_GRAPH_KEY: str = "__WAVEFORM_GRAPH__"
    CHANGE_AUDIO_BUTTON_KEY: str = "__CHANGE__"
    AUDIO_PULLDOWN_KEY: str = "__AUDIO__"
    RESULT_TEXT_KEY: str = "__RESULT__"
    TABLE_DOUBLE_CLICK: str = "__double_click__"


class Viwer:
    def __init__(
        self,
        word_list: List,
        pulldown_list: List,
        pulldown_list_default_idx: int = 0,
        timeout: int = 10,
    ) -> None:
        """Initialize

        Args:
            word_list (List): テーブル表示用のテキストリスト
            pulldown_list (List): プルダウン用のテキストリスト
            pulldown_list_default_idx (int, optional): プルダウンのデフォルトIndex. Defaults to 0.
            timeout (int, optional): event loopのタイムアウト時間[msec]. Defaults to 10.
        """
        self._logger = logging.getLogger("vosk_example_gui.view")
        self.timeout = timeout
        self.window = sg.Window(
            GUI_APP_NAME,
            [
                self._get_waveform_frame(pulldown_list, pulldown_list_default_idx),
                self._get_word_editor_frame(word_list),
            ],
            finalize=True,
        )
        self.window[_GUI_KEY.TABLE_KEY].bind(
            "<Double-Button-1>", _GUI_KEY.TABLE_DOUBLE_CLICK
        )

    def close(self) -> None:
        """GUIをクローズする。"""
        self.window.Close()
        self._logger.info("close window processed")

    def get_event(self) -> Tuple[Event, Any]:
        """GUIイベントを取得する。

        Returns:
            Tuple[Event, Any]: (Event種別, イベントの内容)
        """
        key, content = self.window.read(timeout=self.timeout)
        print(key, content)
        if key == "__TIMEOUT__" or key == _GUI_KEY.TABLE_KEY:
            # 特にEventがない場合
            return Event.NONE, content

        elif key == _GUI_KEY.FILE_LOAD_BUTTON_KEY:
            self.window.FindElement(_GUI_KEY.FILE_PATH_KEY).Update("")
            return Event.LOAD_FILE, content["Browse"]

        elif key == _GUI_KEY.ADD_BUTTON_KEY:
            # ADDボタンが押された場合、テキストボックスの中身を返す
            text = content[_GUI_KEY.INPUT_TEXT_KEY]
            self.window.FindElement(_GUI_KEY.INPUT_TEXT_KEY).Update("")
            return Event.ADD_WORD, text

        elif key == f"{_GUI_KEY.TABLE_KEY}{_GUI_KEY.TABLE_DOUBLE_CLICK}":
            # テーブルの単語がダブルクリックされた場合、対象の単語のインデックスリストを返す
            return Event.DELETE_WORD, content[_GUI_KEY.TABLE_KEY]

        elif key == _GUI_KEY.SUBMIT_BUTTON_KEY:
            # Apply Voskボタンが押された場合
            return Event.SUBMIT_WORDS, ""

        elif key == _GUI_KEY.CHANGE_AUDIO_BUTTON_KEY:
            # Change Audio Sourceボタンが押された場合、選択されているプルダウンの中身を返す
            return Event.CHANGE_AUDIO, content[_GUI_KEY.AUDIO_PULLDOWN_KEY]

        elif key == None or key == sg.WIN_CLOSED:
            # GUIが閉じられた場合
            return Event.FINISH, ""
        else:
            self._logger.error(f"unknown event : {key}, {content}")
            return Event.FINISH, ""

    def update_table(self, data: List) -> None:
        """テーブル内容を更新する。

        Args:
            data (List): テーブルに反映するテキストのリスト
        """
        self.window.FindElement(_GUI_KEY.TABLE_KEY).Update(data)

    def update_text(self, text: str) -> None:
        """テキストエリアの内容を更新する。

        Args:
            text (str): 反映するテキスト
        """
        self.window.FindElement(_GUI_KEY.RESULT_TEXT_KEY).Update(
            f"Recognized...\n\n{text}"
        )

    def update_waveform(self, data: np.ndarray) -> None:
        """グラフの波形を更新する。

        Args:
            data (np.ndarray): 波形データ
        """
        self.window[_GUI_KEY.WAVEFORM_GRAPH_KEY].erase()  # 再描画
        self.window[_GUI_KEY.WAVEFORM_GRAPH_KEY].draw_line((0, 150), (512, 150))

        prev_x: Optional[float] = None
        for i, x in enumerate(data[:: len(data) // 512]):
            if i == 512:
                break
            if prev_x is not None:
                # 前の点と現在の点を線で結ぶ
                self.window[_GUI_KEY.WAVEFORM_GRAPH_KEY].draw_line(
                    (i - 1, prev_x * 150 + 150), (i, x * 150 + 150), color="red"
                )
            prev_x = x
    
    def show_error_popup(self, msg: str) -> None:
        """エラーポップアップを表示する。

        Args:
            msg (str): エラー内容
        """
        sg.popup_error(
            msg,
            title="Error"
        )

    def _get_word_editor_frame(self, word_list: List) -> List:
        """下部フレームを初期化する。

        Args:
            word_list (List): テーブルに反映するテキストのリスト

        Returns:
            List: フレーム情報
        """
        preview_frame = [
            sg.Frame(
                "",
                font="Any 15",
                layout=[
                    [
                        sg.Table(
                            values=word_list,
                            headings=["Word"],
                            text_color="black",
                            background_color="#cccccc",
                            col_widths=[25],
                            num_rows=15,
                            key=_GUI_KEY.TABLE_KEY,
                            bind_return_key=True,
                            auto_size_columns=False,
                            vertical_scroll_only=False,
                            enable_events=True,
                        ),
                        sg.Text(
                            "Recognized...\n\n",
                            size=(22, 3),
                            auto_size_text=True,
                            font=("Arial", 13),
                            justification="center",
                            key=_GUI_KEY.RESULT_TEXT_KEY,
                        ),
                    ],
                    [
                        sg.InputText(key=_GUI_KEY.INPUT_TEXT_KEY, size=(10, 1)),
                        sg.Submit(key=_GUI_KEY.ADD_BUTTON_KEY, button_text="ADD WORD"),
                    ],
                    [
                        sg.InputText(key=_GUI_KEY.FILE_PATH_KEY, size=(15, 1)),
                        sg.FileBrowse(), sg.Submit(key=_GUI_KEY.FILE_LOAD_BUTTON_KEY, button_text="LOAD"),
                    ],
                    [
                        sg.Submit(
                            key=_GUI_KEY.SUBMIT_BUTTON_KEY, button_text="Apply Vosk"
                        )
                    ],
                ],
            )
        ]
        return preview_frame

    def _get_waveform_frame(
        self, pulldown_list: List, pulldown_list_default_idx: int
    ) -> List:
        """上部フレームを初期化する。

        Args:
            pulldown_list (List): プルダウンの中身のテキストリスト
            pulldown_list_default_idx (int): デフォルト選択するプルダウンリストのインデックス

        Returns:
            List: フレーム情報
        """
        print(set(pulldown_list), pulldown_list[pulldown_list_default_idx])
        frame = [
            sg.Frame(
                "",
                font="Any 15",
                layout=[
                    [
                        sg.Graph(
                            canvas_size=(232, 125),
                            graph_bottom_left=(0, -10),
                            graph_top_right=(int(1024 / 2), 300),
                            background_color="white",
                            key=_GUI_KEY.WAVEFORM_GRAPH_KEY,
                        ),
                        sg.Combo(
                            pulldown_list,
                            default_value=pulldown_list[pulldown_list_default_idx],
                            size=(28, len(pulldown_list)),
                            key=_GUI_KEY.AUDIO_PULLDOWN_KEY,
                            readonly=True,
                        ),
                    ],
                    [
                        sg.Submit(
                            key=_GUI_KEY.CHANGE_AUDIO_BUTTON_KEY,
                            button_text="Change Audio Source",
                        )
                    ],
                ],
            )
        ]
        return frame
