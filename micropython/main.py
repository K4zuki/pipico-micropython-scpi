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
from usb488 import Usb488Interface

usb488 = Usb488Interface()

usb.device.get().init(usb488,
                      id_product=0x0488,
                      builtin_driver=True,
                      max_power_ma=100,
                      manufacturer_str="MicroPython",
                      product_str="MicroPython USB488 device",
                      )

if False:
    import sys

    from RaspberryScpiPico import RaspberryScpiPico

    gets = sys.stdin.readline
    pico = RaspberryScpiPico()

    while True:
        line = gets().strip()
        if len(line) > 0:
            for _line in line.split(";"):
                pico.parse_and_process(_line)
