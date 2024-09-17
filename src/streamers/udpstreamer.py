import cv2
import numpy as np

import socket
import requests
import json

from typing import List

from .wledstreamer import WLEDStreamer


class UDPWLEDStreamer(WLEDStreamer):
    MESSAGE_TYPE_DNRGB = 4
    MAX_PIXELS_PER_FRAME = 480

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 21324,
        width: int = 0,
        height: int = 0,
        crop: List[int] = [],
        scale: str = "fill",
        interpolation: str = "smooth",
        gamma: float = 0.5,
    ) -> None:
        self._ip = socket.gethostbyname(host)
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        WLEDStreamer.__init__(self, width, height, crop, scale, interpolation, gamma)

    def close(self):
        self._socket.close()

    def sendFrame(self, frame: np.ndarray) -> None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = frame.flatten()

        for start in range(0, int(frame.size / 3), self.MAX_PIXELS_PER_FRAME):
            start_h = start >> 8
            start_l = start & 0xFF

            message = (
                bytes([self.MESSAGE_TYPE_DNRGB, 2, start_h, start_l])
                + frame[(start * 3) : (start + self.MAX_PIXELS_PER_FRAME) * 3]
                .astype("int8")
                .tobytes()
            )

            self._socket.sendto(message, (self._ip, self._port))

    def _loadInfo(self) -> None:
        response = requests.get("http://" + self._ip + "/json/info", timeout=5)
        self._wled_info = json.loads(response.text)
