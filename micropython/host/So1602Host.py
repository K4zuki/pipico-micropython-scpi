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

import time
from halo import Halo

from SO1602OLED import SO1602OLED

CR = 0x0d
LF = 0x0a
SO1602A_ADDR = 0x3c  # 7-bit address


class So1602Host(SO1602OLED):
    def __init__(self, inst, bus=1):
        """

        :param inst:
        :param bus:
        """

        self.inst = inst  # type: pyvisa.resources.SerialInstrument
        self.bus = bus
        self.inst.open()
        self.inst.write(f"I2C{bus}:ADDRess:BIT 0")
        while self.inst.bytes_in_buffer > 0:
            self.inst.read()

    def send_command(self, command):
        self.inst.write(f"I2C{self.bus}:MEMory:WRITE {self.slave_address:02x},00,{command:02x},1")
        while self.inst.bytes_in_buffer > 0:
            _ = self.inst.read()

    def send_data(self, data):
        if data == LF:
            self.line_feed()
            self.send_command(0x80 | (self.line_counter << 5))
        elif data == CR:
            pass
        else:
            self.inst.write(f"I2C{self.bus}:MEMory:WRITE {self.slave_address:02x},40,{data:02x},1")
            while self.inst.bytes_in_buffer > 0:
                _ = self.inst.read()
        return

    def print(self, message=""):
        assert isinstance(message, str)
        lines = message.replace("\r", "").splitlines()
        for line in lines:
            if line != "":
                data = bytes(line, encoding="utf8")
                data_array = "".join([f"{d:02x}" for d in data])
                self.inst.write(f"I2C{self.bus}:MEMory:WRITE {self.slave_address:02x},40,{data_array},1")
            self.line_feed()
            self.send_command(0x80 | (self.line_counter << 5))

        while self.inst.bytes_in_buffer > 0:
            self.inst.read()

    def rom_select(self, rom=0):
        assert rom in range(3)
        self.instructions.FunctionExtra.DISPLAY_LINES_NUMBER_LSB.val = 1
        self.send_command(self.instructions.FunctionExtra.val)
        self.instructions.FunctionSelectB.ROM.val = rom
        self.instructions.FunctionSelectB.OPR.val = 2
        self.send_command(self.instructions.FunctionSelectB.high_byte())
        self.send_data(self.instructions.FunctionSelectB.low_byte())
        self.send_command(self.instructions.Function.val)
        self.send_command(self.instructions.ClearDisplay.val)


if __name__ == '__main__':
    import pyvisa

    port_name = "ASRL7::INSTR"

    rm = pyvisa.ResourceManager("@py")
    inst = pyvisa.resources.SerialInstrument(rm, port_name)

    oled = So1602Host(inst, 1)
    oled.reset()
    oled.send_command(oled.instructions.ClearDisplay.val)

    oled.instructions.DisplayStatus.CURSOR_BLINK_ENABLE.val = 0
    oled.send_command(oled.instructions.DisplayStatus.val)
    with Halo():
        for rom in range(3):
            oled.rom_select(rom)
            time.sleep(0.1)
            for d in range(256):
                oled.instructions.DDRamAddress.AC.val = 0
                oled.send_command(oled.instructions.DDRamAddress.val)
                time.sleep(0.02)
                oled.send_data(d)
                time.sleep(0.02)
    oled.instructions.DisplayStatus.CURSOR_BLINK_ENABLE.val = 1
    oled.send_command(oled.instructions.DisplayStatus.val)
