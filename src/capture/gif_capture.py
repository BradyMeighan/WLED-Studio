# src/capture/gif_capture.py

import cv2
import numpy as np
import time
import logging
from PIL import Image
from src.utils.logger_handler import logger_handler

class GIFCapture:
    def __init__(self, gif_path: str, fps: int):
        self.logger = logging.getLogger("GIFCapture")
        self.logger.debug(f"Loading GIF from {gif_path}")
        try:
            self.gif = Image.open(gif_path)
        except Exception as e:
            self.logger.error(f"Unable to open GIF file {gif_path}: {e}")
            raise ValueError(f"Unable to open GIF file {gif_path}: {e}")

        self.frame_count = getattr(self.gif, "n_frames", 1)
        self.current_frame = 0
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.last_frame_time = time.perf_counter()

        # Preload all frames
        self.frames = []
        try:
            for i in range(self.frame_count):
                self.gif.seek(i)
                frame = self.gif.convert('RGB')
                frame_np = np.array(frame)
                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                self.frames.append(frame_bgr)
            self.logger.debug(f"Preloaded {len(self.frames)} frames from GIF")
        except EOFError:
            self.logger.error("Reached end of GIF unexpectedly.")
            raise ValueError("Reached end of GIF unexpectedly.")

    def read(self):
        current_time = time.perf_counter()
        elapsed_time = current_time - self.last_frame_time
        if elapsed_time >= self.frame_interval:
            self.last_frame_time = current_time
            self.current_frame = (self.current_frame + 1) % self.frame_count
        frame = self.frames[self.current_frame]
        return frame

    def stop(self):
        self.logger.debug("Stopping GIFCapture and closing GIF file")
        try:
            self.gif.close()
        except Exception as e:
            self.logger.warning(f"Error closing GIF file: {e}")
