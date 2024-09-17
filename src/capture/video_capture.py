# src/capture/video_capture.py

import logging
from src.capture.loopablecamgear import LoopableCamGear
from src.utils.logger_handler import logger_handler

class VideoCapture(LoopableCamGear):
    def __init__(self, source, loop=False, logger=None):
        stream_mode = False
        options = {}
        if isinstance(source, str) and "://" in source:
            stream_mode = True
            options = {"STREAM_RESOLUTION": "360p"}

        self.logger = logger or logging.getLogger("VideoCapture")
        self.logger.debug(f"Initializing VideoCapture with source={source}, loop={loop}, stream_mode={stream_mode}")
        
        try:
            super().__init__(
                source=source,
                stream_mode=stream_mode,
                logging=True,
                loop=loop,
                **options
            )
        except ValueError:
            self.logger.info("Source is not a URL that yt_dlp can handle.")
            super().__init__(
                source=source,
                logging=True,
                loop=loop,
            )
        self.start()
