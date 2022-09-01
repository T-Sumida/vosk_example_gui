import logging
import queue
import sys
from typing import Any, Dict, Optional, Tuple

import numpy as np
import sounddevice as sd
from vosk_example_gui.config import BLOCK_SIZE


class Audio(object):
    def __init__(self) -> None:
        """Initialize"""
        self._logger = logging.getLogger("vosk_example.audio")
        self.q = queue.Queue()
        self.is_streaming = False
        self._sampling_rate = None

    def start_streaming(self, dev_id: Optional[int] = None) -> None:
        """Streamingを開始する

        Args:
            dev_id (Optional[int], optional): デバイスID. Defaults to None.
        """
        if self.is_streaming:
            self.stop()

        device_info = sd.query_devices(dev_id, "input")
        # soundfile expects an int, sounddevice provides a float:
        self._sampling_rate = int(device_info["default_samplerate"])
        self.stream = sd.RawInputStream(
            samplerate=self._sampling_rate,
            blocksize=BLOCK_SIZE,
            device=dev_id,
            dtype="int16",
            channels=1,
            callback=self.__audio_callback,
        )
        self._logger.info(f"device: {dev_id}, sampling_rate: {self._sampling_rate}")
        self.start()

    def get_input_devices(self) -> Tuple[Dict, int]:
        """入力デバイスの情報を返す

        Returns:
            Tuple[Dict, int]: (入力デバイス情報, デフォルトデバイスIndex)
        """
        input_device_config = {}

        device_config_list = sd.query_devices()
        for device_config in device_config_list:
            if (
                device_config["max_input_channels"] > 0
                and device_config["name"] not in input_device_config.keys()
            ):
                input_device_config[device_config["name"]] = device_config["index"]
                print("audio: ", device_config["name"], device_config["index"])

        default_input_idx = sd.query_devices(None, "input")["index"]

        return input_device_config, default_input_idx

    def get_sampling_rate(self) -> Optional[int]:
        """サンプリングレートを返す

        Returns:
            int: サンプリングレート
        """
        return self._sampling_rate

    def start(self) -> None:
        """ストリーミング開始"""
        if not self.is_streaming:
            self.q.queue.clear()
            self.stream.start()
            self._logger.info("start audio streaming")
            self.is_streaming = True

    def stop(self) -> None:
        """ストリーミング停止"""
        if self.is_streaming:
            self.stream.stop()
            self._logger.info("stop audio streaming")
            self.is_streaming = False

    def get(self) -> Optional[bytes]:
        """マイク入力データを返す

        Returns:
            Optional[bytes]: バイト配列
        """
        try:
            data = self.q.get_nowait()
            return data
        except:
            return None

    def __audio_callback(
        self, indata: np.ndarray, frames: int, time: Any, status: Any
    ) -> None:
        """信号入力用コールバック
        Arguments:
            indata {numpy.array} -- 信号
            frames {int} -- 信号のサイズ
            time {CData} -- ADCキャプチャ時間
            status {CallbackFlags} -- エラー収集用のフラグ
        """
        if status:
            print("[audio callback error] {}".format(status))
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))
