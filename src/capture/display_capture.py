from vidgear.gears import ScreenGear

import time

class DisplayCapture(ScreenGear):
    def __init__(self, monitor=None, backend=None, colorspace=None, logging=False, **options) -> None:
        super().__init__(
            monitor, "dxcam", colorspace, logging, **options
        )

        self.start()

    def read(self):
        result = super().read()
        time.sleep(0.1)

        return result