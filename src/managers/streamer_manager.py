# src/managers/streamer_manager.py

import logging
from ..streamers.udpstreamer import UDPWLEDStreamer
from ..streamers.serialstreamer import SerialWLEDStreamer

class StreamerManager:
    def __init__(self, stream_configs: list, logger: logging.Logger = None):
        self.streamers = []
        self.logger = logger or logging.getLogger("StreamerManager")
        for config in stream_configs:
            if "serialport" in config and config["serialport"]:
                self.logger.debug(f"Initializing SerialWLEDStreamer with config: {config}")
                streamer = SerialWLEDStreamer(**config)
            else:
                self.logger.debug(f"Initializing UDPWLEDStreamer with config: {config}")
                streamer = UDPWLEDStreamer(**config)
            self.streamers.append(streamer)

    def process_and_send_frame(self, frame, debug: bool = False):
        for index, streamer in enumerate(self.streamers):
            self.logger.debug(f"Processing frame for streamer {index}")
            stream_frame = streamer.cropFrame(frame)
            stream_frame = streamer.scaleFrame(stream_frame)
            stream_frame = streamer.gammaCorrectFrame(stream_frame)
            streamer.sendFrame(stream_frame)

    def close_all(self):
        for index, streamer in enumerate(self.streamers):
            self.logger.debug(f"Closing streamer {index}")
            streamer.close()
