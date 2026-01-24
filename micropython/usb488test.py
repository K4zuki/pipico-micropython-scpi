import usb.device
from usb.device.usb488 import Usb488Interface

usb488 = Usb488Interface()

usb.device.get().init(usb488,
                      id_product=0x0488,
                      builtin_driver=True,
                      max_power_ma=100,
                      manufacturer_str="MicroPython",
                      product_str="MicroPython USB488 device",
                      )
