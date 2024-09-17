# src/capture/video_file_capture.py

import cv2
import logging
from src.utils.logger_handler import logger_handler

class VideoFileCapture:
    def __init__(self, video_path: str, loop: bool = False):
        self.logger = logging.getLogger("VideoFileCapture")
        self.logger.debug(f"Loading video from {video_path}")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.logger.error(f"Unable to open video file {video_path}")
            raise ValueError(f"Unable to open video file {video_path}")
        self.loop = loop
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 if FPS not available
        self.logger.debug(f"Video FPS: {self.fps}, Total Frames: {self.frame_count}")

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            if self.loop:
                self.logger.debug("Looping video.")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.error("Failed to read frame after looping.")
                    return None
            else:
                self.logger.debug("End of video reached.")
                return None
        return frame.copy()

    def stop(self):
        self.logger.debug("Stopping VideoFileCapture and releasing video file.")
        self.cap.release()
