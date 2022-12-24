from micropython import const
import time
import sys

from machine import I2C, Pin, PWM, SPI

import GpakMux
from EMU2751A import EMU2751A
from AQM0802 import AQM0802, AQM0802_ADDR
from SO1602OLED import SO1602OLED, SO1602A_ADDR
from hd44780compat import BitField, Register, CGFont

led = Pin(25, Pin.OUT)
getc = sys.stdin.read
gets = sys.stdin.readline
putc = sys.stdout.write
u2751a = None
monitor = None

bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=200_000)

# oled.fill(0)
# oled.fill_rect(0, 0, 32, 32, 1)
# oled.fill_rect(2, 2, 28, 28, 0)
# oled.vline(9, 8, 22, 1)
# oled.vline(16, 2, 22, 1)
# oled.vline(23, 8, 22, 1)
# oled.fill_rect(26, 24, 2, 4, 1)
# oled.text('MicroPython', 40, 0, 1)
# oled.text('SSD1306', 40, 12, 1)
# oled.text('OLED 128x64', 40, 24, 1)
# oled.show()
if AQM0802_ADDR in bus.scan():
    rst = Pin(17, mode=Pin.OUT, value=1)
    backlight = PWM(Pin(14, mode=Pin.OUT))
    monitor = AQM0802(bus, backlight)

elif SO1602A_ADDR in bus.scan():
    monitor = SO1602OLED(bus)

for i in range(4):
    if GpakMux.SLG46826_ADDR | (i << 5) in bus.scan():
        print(f"GpakMux #{i} found")
        mux = GpakMux.GpakMux(bus, i)
        u2751a = EMU2751A(mux)
        break

csr = Pin(8, mode=Pin.OUT, value=1)  # orange
csl = Pin(9, mode=Pin.OUT, value=0)  # yellow
spi = SPI(1, 5_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))  # Gray, Purple, Brown

header = [0b001_00000]
lineno = [0b1010_1010]
shifter = [0x00] * 2

csl.value(1)
time.sleep_us(100)
spi.write(bytearray(header + lineno + shifter))
time.sleep_us(100)
csl.value(0)

header = [0b100_00000]
for line in range(10, 100):
    header = [0b100_00000]
    lineno = [line]
    data = [0xff ^ line] * 50
    shifter = [0x00] * 2

    csl.value(1)
    spi.write(bytearray(header + lineno + data + shifter))
    csl.value(0)


def send():
    csl.value(1)
    spi.write(bytearray(header + lineno + data + shifter))
    time.sleep_us(200)
    csl.value(0)


if u2751a is not None:
    while True:
        line = gets().strip()
        if len(line) > 0:
            for c in line.encode("utf8"):
                monitor.send_data(int(c))
            monitor.send_data(0x0a)
            u2751a.parse_and_process(line)

monitor.instructions.CGRamAddress.AC.val = ROW << 3
monitor.send_command(monitor.instructions.CGRamAddress.val)
monitor.send_data(0x1f)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)

monitor.instructions.CGRamAddress.AC.val = OPEN_UPPER_ROW << 3
monitor.send_command(monitor.instructions.CGRamAddress.val)
monitor.send_data(0x1f)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x00)
monitor.send_data(0x01)

monitor.instructions.CGRamAddress.AC.val = OPEN_LOWER_ROW << 3
monitor.send_command(monitor.instructions.CGRamAddress.val)
monitor.send_data(0x1f)
monitor.send_data(0x01)
monitor.send_data(0x01)
monitor.send_data(0x01)
monitor.send_data(0x01)
monitor.send_data(0x01)
monitor.send_data(0x01)
monitor.send_data(0x01)

monitor.instructions.CGRamAddress.AC.val = CLOSE_UPPER_ROW << 3
monitor.send_command(monitor.instructions.CGRamAddress.val)
monitor.send_data(0x1f)
monitor.send_data(0x10)
monitor.send_data(0x10)
monitor.send_data(0x08)
monitor.send_data(0x04)
monitor.send_data(0x02)
monitor.send_data(0x01)
monitor.send_data(0x01)

monitor.instructions.CGRamAddress.AC.val = CLOSE_LOWER_ROW << 3
monitor.send_command(monitor.instructions.CGRamAddress.val)
monitor.send_data(0x1f)
monitor.send_data(0x11)
monitor.send_data(0x11)
monitor.send_data(0x09)
monitor.send_data(0x05)
monitor.send_data(0x03)
monitor.send_data(0x01)
monitor.send_data(0x01)

monitor.cls()
