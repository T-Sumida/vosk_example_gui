import sys
import queue
import logging
import sounddevice as sd

from typing import Optional, List

_BLOCK_SIZE = 8000


class Audio(object):

    def __init__(self, dev_id: Optional[int]):
        """Initialize

        Args:
            dev_id (Optional[int]): デバイス情報（Noneの場合はデフォルトマイクを使用）
        """
        self._logger = logging.getLogger("vosk_example.audio")
        self.q = queue.Queue()
        self.is_streaming = False

        # リアルタイム用初期化
        device_info = sd.query_devices(dev_id, 'input')
        # soundfile expects an int, sounddevice provides a float:
        self._sampling_rate = int(device_info['default_samplerate'])
        self.__init_realtime(dev_id, self._sampling_rate)


    def start_streaming(self, dev_id: Optional[int] = None) -> None:
        if self.is_streaming:
            self.stop()

        device_info = sd.query_devices(dev_id, 'input')
        # soundfile expects an int, sounddevice provides a float:
        self._sampling_rate = int(device_info['default_samplerate'])
        self._logger.debug(f"device: {dev_id}, sampling_rate: {self.sampling_rate}")
        self.stream = sd.RawInputStream(
            samplerate=self.sampling_rate,
            blocksize=_BLOCK_SIZE,
            device=dev_id, dtype='int16',
            channels=1, callback=self.__audio_callback
        )
        self.start()

    def get_input_devices(self) -> List:
        input_device_config = []

        device_config_list = sd.query_devices()
        for device_config in device_config_list:
            if device_config["max_input_channels"] > 0:
                input_device_config.append({
                    "name": device_config["name"],
                    "idx": device_config["index"]
                })
        
        return input_device_config

    def get_sampling_rate(self) -> int:
        """サンプリングレートを返す

        Returns:
            int: サンプリングレート
        """
        return self._sampling_rate

    def __init_realtime(self, dev_id: Optional[int], sampling_rate: int):
        """ストリームを初期化

        Args:
            dev_id (Optional[int]): デバイス情報
            sampling_rate (int): サンプリングレート
        """
        self._logger.debug(f"device: {dev_id}, sampling_rate: {sampling_rate}")
        self.stream = sd.RawInputStream(
            samplerate=sampling_rate,
            blocksize=_BLOCK_SIZE,
            device=dev_id, dtype='int16',
            channels=1, callback=self.__audio_callback
        )
        self.q = queue.Queue()

    def start(self):
        """ストリーミング開始"""
        if not self.is_streaming:
            self.q.queue.clear()
            self.stream.start()
            self._logger.info("start audio streaming")
            self.is_streaming = True

    def stop(self):
        """ストリーミング停止"""
        if self.is_streaming:
            self.stream.stop()
            self._logger.info("stop audio streaming")
            self.is_streaming = False

    def get(self) -> bytes:
        """マイク入力データを返す

        Returns:
            bytes: バイト配列
        """
        data = self.q.get()
        return data

    def __audio_callback(self, indata, frames, time, status):
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