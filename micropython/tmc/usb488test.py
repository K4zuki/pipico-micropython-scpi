import usb.device
from Usb488ScpiPico import Usb488ScpiPico
from RaspberryScpiPico import RaspberryScpiPico

pico = RaspberryScpiPico()
usb488if = Usb488ScpiPico(pico)

usb.device.get().init(usb488if,
                      id_product=0x0488,
                      builtin_driver=True,
                      max_power_ma=100,
                      manufacturer_str="MicroPython",
                      product_str="MicroPython USB488 device",
                      )
