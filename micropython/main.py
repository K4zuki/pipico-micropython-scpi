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
u2751a = EMU2751A()


def main():
    while True:
        ch = getc(1)
        print("Got " + hex(ord(ch)))


def readline(p1=False, loopback=False, diag=False):
    if p1:
        print("# ", end="")
    stack = [getc(1)]

    while True:
        ch = getc(1)
        if ch == '\n':
            break
        else:
            stack.append(ch)

            led.value(0)
            time.sleep_us(100)
            led.value(1)
            time.sleep_us(100)
            led.value(0)
            if loopback:
                putc(ch)

    read_line = "".join(stack).strip()
    if diag:
        print("", end="\r")
        print(">", read_line, "?" in read_line, len(read_line))
    return read_line


def shell():
    while True:
        line = readline().strip()
        if len(line) > 0:
            u2751a.parse_and_process(line)


bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=60_000)

if __name__ == '__main__':

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

            for row in [1, 2]:
                for col in [1, 2, 3, 4, 5, 6]:
                    mux.connect(row, col)
                    time.sleep(0.01)

    shell()
