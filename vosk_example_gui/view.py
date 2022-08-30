from enum import Enum
from typing import Tuple, Dict, List

import PySimpleGUI as sg

from vosk_example_gui.config import GUI_APP_NAME


class Event(Enum):
    FINISH: int = 0



class Viwer:
    def __init__(self, timeout: int = 1) -> None:
        self.timeout = timeout
        self.window = sg.Window(
            GUI_APP_NAME,
            [self._get_word_editor_frame(), self._get_waveform_frame()],
            finalize=True
        )
        self.window["TOPIC_KEY"].bind('<Double-Button-1>' , "+-double click-")

    def close(self) -> None:
        self.window.Close()

    def get_event(self) -> Tuple[str, Dict]:
        return self.window.read(timeout=self.timeout)

    def update_waveform(self, data: List):
        self.window["-GRAPH-"].erase()  # 再描画
        self.window["-GRAPH-"].draw_line((0, 64), (224, 64))

        prev_x = None
        for i, x in enumerate(data[::len(data)//224]):
            if i == 224: break
            if prev_x is not None:
                # 前の点と現在の点を線で結ぶ
                self.window["-GRAPH-"].draw_line((i-1, prev_x), (i, x), color="red")
            prev_x = x
    
    def _get_word_editor_frame(self) -> List:
        preview_frame = [sg.Frame('', font='Any 15', layout=[
            [
                sg.Table(
                    values=["hello"],
                    headings=["Word"],
                    text_color="black",
                    background_color="#cccccc",
                    col_widths=[12],
                    num_rows=15,
                    key="TOPIC_KEY",
                    bind_return_key=True,
                    auto_size_columns=False,
                    vertical_scroll_only=False,
                    enable_events=True,
                )
            ],
            [sg.InputText(key="__TOPIC_KEY__", size=(10, 1)),
                     sg.Submit(key="__ADD__", button_text="ADD")],
            [sg.Submit(key="__SUBMIT__")]

        ])]
        return preview_frame

    def _get_waveform_frame(self) -> List:
        frame = [sg.Frame('', font='Any 15', layout=[
            [sg.Graph(
                        canvas_size=(224, 128),
                        graph_bottom_left=(0, -10),
                        graph_top_right=(int(1024 / 2), 300),
                        background_color="white",
                        key="-GRAPH-",
                    )]
        ])]
        return frame


    def _get_edit_frame(self) -> List:
        """編集画面用のPysimpleGUI.Frameを構成する.
        Returns:
            List: [sg.Frame]
        """
        edit_frame = [
            sg.Frame(
                "Edit", font='Any 15', layout=[
                    # [sg.Text("TOPIC NAME : "),
                    #  sg.InputText(key="__TOPIC_KEY__")],
                    [sg.Submit(key="__SUBMIT__"), sg.Submit(
                        key="__CLEAR___", button_text="Clear")]
                ]
            )
        ]
        return edit_frame