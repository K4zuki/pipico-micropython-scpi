"""
MIT License

Copyright (c) 2023 Kazuki Yamamoto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import usb.device
from Usb488ScpiPico import Usb488ScpiPico
from RaspberryScpiPico import RaspberryScpiPico

pico = RaspberryScpiPico()
usb488if = Usb488ScpiPico(pico)

usb.device.get().init(usb488if,
                      id_product=0x0488,
                      builtin_driver=False,
                      max_power_ma=100,
                      manufacturer_str="MicroPython",
                      product_str="MicroPython USB488 device",
                      )

from machine import UART
import os

uart = UART(0)
os.dupterm(uart, 0)
uart.irq(os.dupterm_notify, UART.IRQ_RXIDLE)
