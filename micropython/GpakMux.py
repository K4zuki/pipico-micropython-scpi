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
import sys

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List
from collections import namedtuple
from machine import I2C
import time

SLG46826_ADDR = 0x08  # 7-bit addressing
WRITE_REG = 0x7A
P0_REG = 0x76
P1_REG = 0x79


class Bit(namedtuple("Bit", ["reading_bit", "writing_bit"])):
    val = 0


class Port:
    write_address = WRITE_REG
    read_address = 0
    mask = 0
    bit0 = Bit(0, 0)
    bit1 = Bit(1, 1)
    bit2 = Bit(2, 2)
    bit3 = Bit(3, 3)
    bit4 = Bit(4, 4)
    bit5 = Bit(5, 5)

    def __init__(self, _bus, address):
        self.address = address
        self.bus = _bus  # type: I2C
        self.bits = [self.bit0,
                     self.bit1,
                     self.bit2,
                     self.bit3,
                     self.bit4,
                     self.bit5]

    def get_bit(self, bit):
        assert 6 > bit >= 0
        return self.bits[bit].val

    def set_bit(self, bit, value):
        assert 6 > bit >= 0
        self.bits[bit].val = value

    def send(self):

        self.bits = [self.bit0,
                     self.bit1,
                     self.bit2,
                     self.bit3,
                     self.bit4,
                     self.bit5]

        data = 0
        for _bit in self.bits:
            data = data | (_bit.val << _bit.writing_bit)
        data = (data & 0x3F) | (self.mask << 6)
        clock = data | 0xC0

        self.bus.writeto(self.address, bytes([self.write_address, clock]))
        self.bus.writeto(self.address, bytes([self.write_address, data]))

    def write(self, data):
        assert 256 > data >= 0
        [self.set_bit(sft, 0x01 & (data >> sft)) for sft in range(6)]
        self.send()

    def read(self):
        data = self.bus.readfrom_mem(self.address, self.read_address, 1)[0]
        for bit in self.bits:
            bit.val = 0x01 & (data >> bit.reading_bit)
        return data


class Row(namedtuple("Row", ["col5", "col4", "col3", "col2", "col1", "col0"])):
    """
    """

    def byte(self):
        return


class GpakMux:
    max_row = 2
    max_col = 6

    def __init__(self, bus, address):
        assert 0 <= address < 4
        self.address = SLG46826_ADDR | (address << 6)
        self.bus = bus  # type: I2C

        self.port0 = Port(self.bus, self.address)
        self.port0.read_address = P0_REG
        self.port0.mask = 1
        self.port0.bit0 = Bit(2, 0)
        self.port0.bit1 = Bit(3, 1)
        self.port0.bit2 = Bit(4, 2)
        self.port0.bit3 = Bit(5, 3)
        self.port0.bit4 = Bit(6, 4)
        self.port0.bit5 = Bit(7, 5)

        self.port1 = Port(self.bus, self.address)
        self.port1.read_address = P1_REG
        self.port1.mask = 2

        self.cross_points = {
            1: {  # ROW
                1: (self.port1, 0),  # COL
                2: (self.port1, 2),
                3: (self.port1, 4),
                4: (self.port0, 5),
                5: (self.port0, 3),
                6: (self.port0, 1),
            },
            2: {  # ROW
                1: (self.port1, 1),  # COL
                2: (self.port1, 3),
                3: (self.port1, 5),
                4: (self.port0, 4),
                5: (self.port0, 2),
                6: (self.port0, 0),
            }
        }
        self.disconnect_all()

    def int_to_rowcol(self, num):
        row = num // 100
        col = num % 100
        assert self.max_row >= row >= 1
        assert self.max_col >= col >= 1
        return row, col

    def connect(self, row, column):
        port, bit = self.cross_points[row][column]
        port.set_bit(bit, 1)
        port.send()

    def disconnect(self, row, column):
        port, bit = self.cross_points[row][column]
        port.set_bit(bit, 0)
        port.send()

    def disconnect_all(self):
        self.port0.write(0x00)
        self.port1.write(0x00)

    def query(self, row, column):
        port, bit = self.cross_points[row][column]

        stat = port.get_bit(bit)

        return stat


def main(bus):
    mux = GpakMux(bus, 0)
    for row in [1, 2]:
        for col in [1, 2, 3, 4, 5, 6]:
            print("connect", row, col)
            mux.connect(row, col)
            time.sleep(0.5)
            print("disconnect", row, col)
            mux.disconnect(row, col)
            time.sleep(0.5)


if __name__ == '__main__':
    bus = I2C(1)
    main(bus)
