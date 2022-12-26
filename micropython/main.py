import sys

from machine import I2C, Pin, PWM, SPI

import GpakMux
from EMU2751A import EMU2751A

gets = sys.stdin.readline

led = Pin(25, Pin.OUT)
bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=200_000)

for i in range(4):
    if GpakMux.SLG46826_ADDR | (i << 5) in bus.scan():
        print(f"GpakMux #{i} found")
        mux = GpakMux.GpakMux(bus, i)
        u2751a = EMU2751A(mux)
        break
else:
    u2751a = None

if u2751a is not None:
    while True:
        line = gets().strip()
        if len(line) > 0:
            u2751a.parse_and_process(line)
