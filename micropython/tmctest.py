import os
import time
import usb.device
from usb.device.tmc import TMCInterface

tmc = TMCInterface()

usb.device.get().init(tmc, builtin_driver=True)
