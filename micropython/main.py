import time
import sys

from machine import I2C, Pin, PWM

import GpakMux
from EMU2751A import EMU2751A
from AQM0802 import AQM0802, AQM0802_ADDR
from SO1602OLED import SO1602OLED, SO1602A_ADDR
from hd44780compat import BitField, Register

led = Pin(25, Pin.OUT)
getc = sys.stdin.read
gets = sys.stdin.readline
putc = sys.stdout.write
u2751a = None

bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=60_000)

if AQM0802_ADDR in bus.scan():
    rst = Pin(17, mode=Pin.OUT, value=1)
    backlight = PWM(Pin(14, mode=Pin.OUT))
    aqm = AQM0802(bus, backlight)

    for c in "Hello,\nWor\nld!".encode("utf8"):
        aqm.send_data(int(c))

if SO1602A_ADDR in bus.scan():
    oled = SO1602OLED(bus)

    for c in "Hello,\nWor\nld!".encode("utf8"):
        oled.send_data(int(c))

for i in range(4):
    if GpakMux.SLG46826_ADDR | (i << 5) in bus.scan():
        print(f"GpakMux #{i} found")
        mux = GpakMux.GpakMux(bus, i)
        u2751a = EMU2751A(mux)
        break

if u2751a is not None:
    while True:
        line = gets().strip()
        if len(line) > 0:
            u2751a.parse_and_process(line)
