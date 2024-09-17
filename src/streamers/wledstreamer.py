import cv2
import numpy as np

import math
import logging
import sys

from typing import List

# Correct: This imports the function directly
from src.utils.logger_handler import logger_handler




class WLEDStreamer:
    def __init__(
        self,
        width: int = 0,
        height: int = 0,
        crop: List[int] = [],
        scale: str = "fill",
        interpolation: str = "smooth",
        gamma: float = 0.5,
    ) -> None:
        self.logger = logging.getLogger("WLEDStreamer")
        self.logger.propagate = False
        self.logger.addHandler(logger_handler())
        self.logger.setLevel(logging.DEBUG)

        self._wled_info = {}  # type: Dict[str, Any]

        self.width = width
        self.height = height
        if self.width == 0 or self.height == 0:
            self.logger.info("Getting dimensions from wled...")
            self.width, self.height = self._getDimensions()
            self.logger.debug("width: %d, height: %d" % (self.width, self.height))
            if self.width == 0 or self.height == 0:
                self.logger.error(
                    "Could not get width and/or height from wled instance."
                )
                sys.exit()
        self._display_ratio = self.width / self.height

        self.crop = crop
        self.scale = scale

        inverseGamma = 1 / gamma
        self._gamma_table = [((i / 255) ** inverseGamma) * 255 for i in range(256)]
        self._gamma_table = np.array(self._gamma_table, np.uint8)

        self._interpolation = (
            cv2.INTER_NEAREST if interpolation == "hard" else cv2.INTER_AREA
        )

    def close(self):
        pass

    def cropFrame(self, frame: np.ndarray) -> np.ndarray:
        if self.crop:
            frame_height, frame_width = frame.shape[:2]
            frame = frame[
                self.crop[1] : frame_height - self.crop[3],
                self.crop[0] : frame_width - self.crop[2],
            ]

        return frame

    def scaleFrame(self, frame: np.ndarray) -> np.ndarray:
        frame_height, frame_width = frame.shape[:2]

        if self.scale == "stretch":
            frame = cv2.resize(
                frame, (self.width, self.height), interpolation=self._interpolation
            )
        else:
            if self.scale in ["fill", "fit"]:
                image_ratio = frame_width / frame_height

                if (self.scale == "fill" and image_ratio > self._display_ratio) or (
                    self.scale == "fit" and image_ratio < self._display_ratio
                ):
                    size = (math.floor(self.height * image_ratio), self.height)
                else:
                    size = (self.width, math.floor(self.width / image_ratio))
                frame = cv2.resize(frame, size, interpolation=self._interpolation)

            frame_height, frame_width = frame.shape[:2]
            left = math.floor((frame_width - self.width) / 2)
            top = math.floor((frame_height - self.height) / 2)
            frame = frame[top : (top + self.height), left : (left + self.width)]
            # NB: frame could now be smaller than self.width, self.height!
            # see extension below

        frame_height, frame_width = frame.shape[:2]
        if frame_width < self.width or frame_height < self.height:
            left = math.floor((self.width - frame_width) / 2)
            right = self.width - frame_width - left
            top = math.floor((self.height - frame_height) / 2)
            bottom = self.height - frame_height - top
            frame = cv2.copyMakeBorder(
                frame, top, bottom, left, right, cv2.BORDER_CONSTANT, 0
            )

        return frame

    def gammaCorrectFrame(self, frame: np.ndarray) -> np.ndarray:
        return cv2.LUT(frame, self._gamma_table)

    def sendFrame(self, frame: np.ndarray) -> None:
        self.logger.warning("Sending should be handled by a subclass of this class.")

    def _loadInfo(self) -> None:
        pass

    def _getDimensions(self) -> (int, int):
        if not self._wled_info:
            try:
                self._loadInfo()
            except Exception:
                self.logger.warning("Could not get information from WLED.")
                return 0, 0

        try:
            width = self._wled_info["leds"]["matrix"]["w"]
            height = self._wled_info["leds"]["matrix"]["h"]
        except Exception:
            self.logger.warning("Dimensions not found in info from WLED.")
            return 0, 0

        return width, height
