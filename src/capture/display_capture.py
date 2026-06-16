import platform
from vidgear.gears import ScreenGear
import time

class DisplayCapture(ScreenGear):
    def __init__(self, monitor=None, backend=None, colorspace=None, logging=False, **options) -> None:
        if platform.system() == "Windows":
            backend = backend or "dxcam"
        else:
            backend = None      # let ScreenGear fall through to mss
            monitor = monitor or 1   # monitor=1 routes to vidgear's native mss path
        super().__init__(monitor, backend, colorspace, logging, **options)
        self.start()

    def read(self):
        result = super().read()
        time.sleep(0.1)
        return result