import json
import logging
from collections import defaultdict
from typing import Dict, List, Optional

import vosk


class VoskClient:
    def __init__(self) -> None:
        """Initialize"""
        self._logger = logging.getLogger("vosk_example.vosk_client")
        self._rec = None

    def initialize_model(
        self, target_word_list: List, sampling_rate: int, model_path: str
    ) -> None:
        """voskモデルを初期化する。

        Args:
            target_word_list (List): 認識対象のワードリスト（空の場合は通常のモデルを作成）
            sampling_rate (int): 入力される音声データのサンプリングレート
            model_path (str): 利用するモデルのパス
        """
        self._logger.info(f"target words is {target_word_list}")

        # voskの初期化
        self._model = vosk.Model(model_path)
        if len(target_word_list) > 0:
            target_word = '["' + " ".join(target_word_list) + '", "[unk]"]'
            self._rec = vosk.KaldiRecognizer(self._model, sampling_rate, target_word)
        else:
            self._rec = vosk.KaldiRecognizer(self._model, sampling_rate)
        self._rec.SetPartialWords(True)  # confidenceを取得するために必要

        # 途中解析結果のconfidenceを保持するためのDict
        self._partial_response = defaultdict(list)

    def recognize(self, audio_data: bytes) -> Optional[Dict]:
        """音声認識を行う

        Args:
            audio_data (bytes): マイク入力データ

        Returns:
            Optional[Dict]: 結果を格納したDict（Noneの場合は認識できていない）
        """
        if self._rec is None:
            self._logger.error(f"model not initialized.")
            return None

        if self._rec.AcceptWaveform(audio_data):
            return self._judge_final_response()
        else:
            response = json.loads(self._rec.PartialResult())
            if "partial_result" in response.keys():
                for r in response["partial_result"]:
                    word = r["word"]
                    conf = r["conf"]
                    if word not in self._partial_response.keys():
                        self._partial_response[word] = []
                    self._partial_response[word].append(conf)
                    self._logger.debug(f"{word} is {conf}")
            return None

    def _judge_final_response(self) -> Optional[Dict]:
        """Voskの結果をまとめる

        Returns:
            Optional[Dict]: 結果情報
        """
        response = json.loads(self._rec.Result())
        if "text" in response.keys():
            result = {}
            result["result"] = response["text"]
            result["partial_conf"] = []
            for k, v in self._partial_response.items():
                conf = {}
                conf[k] = v
                result["partial_conf"].append(conf)
            self._partial_response = defaultdict(List)
            return result
        else:
            return None
