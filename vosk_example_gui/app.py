from vosk_example_gui.view import Viwer

import PySimpleGUI as sg

class App:
    def __init__(self) -> None:
        self.viewer = Viwer()

    def run(self):
        try:
            while True:
                event = self.viewer.get_event()
                print(event)
                if None in event:
                    break
                if event == sg.WIN_CLOSED:
                    break
        except Exception as e:
            # logger.error(f"Cache Watcher Error : {e}")
            pass
        except KeyboardInterrupt:
            pass
        finally:
            print("close")
            self.viewer.close()
