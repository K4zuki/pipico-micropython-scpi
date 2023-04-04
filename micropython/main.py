import sys
import time

from machine import I2C, Pin, PWM, SPI

# import GpakMux
# from EMU2751A import EMU2751A
from RaspberryScpiPico import RaspberryScpiPico

gets = sys.stdin.readline

led = Pin(25, Pin.OUT)
bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=200_000)

# for i in range(4):
#     if GpakMux.SLG46826_ADDR | (i << 5) in bus.scan():
#         print(f"GpakMux #{i} found")
#         mux = GpakMux.GpakMux(bus, i)
#         u2751a = EMU2751A(mux)
#         break
# else:
#     u2751a = None

csr = Pin(8, mode=Pin.OUT, value=1)  # orange
csl = Pin(9, mode=Pin.OUT, value=0)  # yellow
spi = SPI(1, 5_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))  # Gray, Purple, Brown

header = [0b001_00000]
lineno = [0b1010_1010]
shifter = [0x00] * 2

csl.value(1)
spi.write(bytearray(header + lineno + shifter))
time.sleep_us(1)
csl.value(0)

header = [0b100_00000]
data = [0xc0] * 50


def swap(_line):
    _lineno = 0
    for b in reversed(list(range(8))):
        bb = (((_line >> b) & 1) << (7 - b))
        _lineno |= bb
    return _lineno


csl.value(1)
for line in range(1, 241):
    spi.write(bytearray(header + [swap(line)] + data))
spi.write(bytearray(shifter))
csl.value(0)

# if u2751a is not None:
#     while True:
#         line = gets().strip()
#         if len(line) > 0:
#             u2751a.parse_and_process(line)

pico = RaspberryScpiPico()


def pico_run():
    while True:
        line = gets().strip()
        if len(line) > 0:
            pico.parse_and_process(line)


pico_run()
