import time
import sys

from machine import I2C, Pin

from KeysightU2751AEmu import KeysightU2751AEmu

led = Pin(25, Pin.OUT)
getc = sys.stdin.read
gets = sys.stdin.readline
putc = sys.stdout.write
u2751a = KeysightU2751AEmu()


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


if __name__ == '__main__':
    shell()
