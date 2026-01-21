import os
import time

from machine import UART

uart = UART(0, baudrate=115200, tx=0, rx=1)
os.dupterm(uart)

import usb.device
from usb488 import Usb488Interface

usb488 = Usb488Interface()

usb.device.get().init(usb488,
                      id_product=0x0488,
                      builtin_driver=True,
                      max_power_ma=100,
                      manufacturer_str="MicroPython",
                      product_str="MicroPython USB488 device",
                      )
