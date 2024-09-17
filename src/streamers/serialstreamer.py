import cv2
import numpy as np

import serial
import json

from typing import List

from .wledstreamer import WLEDStreamer


class SerialWLEDStreamer(WLEDStreamer):
    def __init__(
        self,
        serialport: str = "COM3",
        baudrate: int = 115200,
        width: int = 0,
        height: int = 0,
        crop: List[int] = [],
        scale: str = "fill",
        interpolation: str = "smooth",
        gamma: float = 0.5,
    ) -> None:
        self._serial_device = serial.Serial(serialport, baudrate, timeout=1)

        WLEDStreamer.__init__(self, width, height, crop, scale, interpolation, gamma)

    def close(self):
        self._serial_device.close()

    def sendFrame(self, frame: np.ndarray) -> None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = frame.flatten().astype("int8").tobytes()

        header = bytes([0xC9, 0xDA, len(frame) >> 8, len(frame) & 0xFF])
        footer = bytes([0x36])
        message = header + frame + footer

        self._serial_device.write(message)

    def _loadInfo(self) -> None:
        self._serial_device.write(b'{"v":true}')
        response = self._serial_device.readline()
        self._wled_info = json.loads(response)["info"]
