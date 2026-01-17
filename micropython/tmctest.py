import os
import time
import usb.device
from usb488 import TMCInterface

tmc = TMCInterface()

usb.device.get().init(tmc, builtin_driver=True)
