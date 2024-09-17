# src/capture/image_capture.py

import cv2
import logging
from src.utils.logger_handler import logger_handler

class ImageCapture:
    def __init__(self, image_path: str):
        self.logger = logging.getLogger("ImageCapture")
        self.logger.debug(f"Loading image from {image_path}")
        self.image = cv2.imread(image_path)
        if self.image is None:
            self.logger.error(f"Unable to load image from {image_path}")
            raise ValueError(f"Unable to load image from {image_path}")

    def read(self):
        self.logger.debug("Reading image frame")
        return self.image.copy()

    def stop(self):
        self.logger.debug("Stopping ImageCapture (no action needed)")
