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
from hd44780compat import BitField, Register, HD44780Instructions
from AQM0802 import AQM0802, DataCommandSelect

SO1602A_ADDR = 0x3c  # 7-bit address


class LongRegister(Register):
    size = 16

    def high_byte(self):
        val = self.val
        msbyte = 0xff & (val >> 8)
        return msbyte

    def low_byte(self):
        val = self.val
        lsbyte = 0xff & val
        return lsbyte


class DisplayStatusExtra(Register):
    DISPLAY_LINES_NUMBER_MSB = BitField("DISPLAY_LINES_NUMBER_MSB", 1, 0, 0b0, False)
    BLACK_WHITE = BitField("BW", 1, 1, 0b0, False)
    FONT_WIDTH = BitField("FW", 1, 2, 0b0, False)

    @property
    def fields(self):
        return (self.DISPLAY_LINES_NUMBER_MSB,
                self.BLACK_WHITE,
                self.FONT_WIDTH,
                BitField("CONST", 5, 3, 0b00001, True)
                )


class Function(Register):
    INSTRUCTION_TABLE = BitField("INSTRUCTION_TABLE", 1, 0, 0b00, False)
    FONT_SELECTION = BitField("FONT_SELECTION", 1, 2, 0b0, False)
    DISPLAY_LINES_NUMBER_LSB = BitField("DISPLAY_LINES_NUMBER_LSB", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (self.INSTRUCTION_TABLE,
                BitField("RE0", 1, 1, 0b0, True),
                self.FONT_SELECTION,
                self.DISPLAY_LINES_NUMBER_LSB,
                BitField("CONST", 4, 4, 0b0010, True),
                )


class FunctionExtra(Register):
    REVERSE = BitField("REVERSE", 1, 0, 0b0, False)
    CGRAM_BLiNK_ENABLE = BitField("CGRAM_BLiNK_ENABLE", 1, 2, 0b0, False)
    DISPLAY_LINES_NUMBER_LSB = BitField("DISPLAY_LINES_NUMBER_LSB", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (self.REVERSE,
                BitField("RE1", 1, 1, 0b1, True),
                self.CGRAM_BLiNK_ENABLE,
                self.DISPLAY_LINES_NUMBER_LSB,
                BitField("CONST", 4, 4, 0b0010, True),
                )


class EntryModeExtra(Register):
    BDS = BitField("BDS", 1, 0, 0b1, False)
    BDC = BitField("BDC", 1, 1, 0b0, False)

    @property
    def fields(self):
        return (self.BDS,
                self.BDC,
                BitField("CONST", 6, 2, 0b000001, True),
                )


class DoubleHeightShiftScroll(Register):
    SHIFT_SCROLL = BitField("SHIFT_SCROLL", 1, 0, 0b0, False)
    UD = BitField("UD", 2, 2, 0b0, False)

    @property
    def fields(self):
        return (self.SHIFT_SCROLL,
                BitField("CONST", 1, 1, 0b0, True),
                self.UD,
                BitField("CONST", 4, 4, 0b0001, True),
                )


class ScrollQuantity(Register):
    """Set the quantity of horizontal dot scroll. (POR=00 0000)

    *Valid up to SQ[5:0] = 110000b*
    """
    SCROLL_QTY = BitField("SCROLL_QTY", 6, 0, 0b000_000, False)

    @property
    def fields(self):
        return (self.SCROLL_QTY,
                BitField("CONST", 2, 6, 0b10, True),
                )


class ShiftEnable(Register):
    DISPLAY_SHIFT1 = BitField("DISPLAY_SHIFT1", 1, 0, 0b1, False)
    DISPLAY_SHIFT2 = BitField("DISPLAY_SHIFT2", 1, 1, 0b1, False)
    DISPLAY_SHIFT3 = BitField("DISPLAY_SHIFT3", 1, 2, 0b1, False)
    DISPLAY_SHIFT4 = BitField("DISPLAY_SHIFT4", 1, 3, 0b1, False)

    @property
    def fields(self):
        return (self.DISPLAY_SHIFT1,
                self.DISPLAY_SHIFT2,
                self.DISPLAY_SHIFT3,
                self.DISPLAY_SHIFT4,
                BitField("CONST", 4, 4, 0b0001, True),
                )


class ScrollEnable(Register):
    HORIZONTAL_SMOOTH1 = BitField("HORIZONTAL_SMOOTH1", 1, 0, 0b1, False)
    HORIZONTAL_SMOOTH2 = BitField("HORIZONTAL_SMOOTH2", 1, 1, 0b1, False)
    HORIZONTAL_SMOOTH3 = BitField("HORIZONTAL_SMOOTH3", 1, 2, 0b1, False)
    HORIZONTAL_SMOOTH4 = BitField("HORIZONTAL_SMOOTH4", 1, 3, 0b1, False)

    @property
    def fields(self):
        return (self.HORIZONTAL_SMOOTH1,
                self.HORIZONTAL_SMOOTH2,
                self.HORIZONTAL_SMOOTH3,
                self.HORIZONTAL_SMOOTH4,
                BitField("CONST", 4, 4, 0b0001, True),
                )


class OLEDModeEntry(Register):
    OLED_COMMANDSET_ENABLE = BitField("SD", 1, 0, 0b0, False)

    @property
    def fields(self):
        return (self.OLED_COMMANDSET_ENABLE,
                BitField("CONST", 7, 1, 0b0111_100, True),
                )


class ContrastControl(LongRegister):
    """Set Contrast Control
    """
    CONTRAST = BitField("CONTRAST", 8, 0, 0x7f, False)

    @property
    def fields(self):
        return (self.CONTRAST,
                BitField("CONST", 8, 8, 0x8a, True),
                )


class ClockControl(LongRegister):
    """Set Display Clock Divide Ratio/Oscillator Frequency

    A[3:0]: Define the divide ratio (D) of the display clocks (DCLK): divide ratio = A[3:0] + 1 (POR=0000b)
    """
    DIVIDE_RATIO = BitField("DIVIDE_RATIO", 8, 0, 0b0000, False)
    FREQUENCY = BitField("FREQUENCY", 8, 0, 0b0111, False)

    @property
    def fields(self):
        return (self.DIVIDE_RATIO,
                self.FREQUENCY,
                BitField("CONST", 8, 8, 0xd5, True),
                )


class FunctionSelectA(LongRegister):
    A = BitField("A", 8, 0, 0x5c, False)

    @property
    def fields(self):
        return (self.A,
                BitField("CONST", 8, 8, 0x71, True),
                )


class FunctionSelectB(LongRegister):
    OPR = BitField("OPR", 2, 0, 0b00, False)
    ROM = BitField("ROM", 2, 2, 0b00, False)

    @property
    def fields(self):
        return (self.OPR,
                self.ROM,
                BitField("CONST", 4, 4, 0b0000, True),
                BitField("CONST", 8, 8, 0x72, True),
                )


class PhaseLength(LongRegister):
    PHASE1_PERIOD = BitField("PHASE1_PERIOD", 4, 0, 0b1000, False)
    PHASE2_PERIOD = BitField("PHASE2_PERIOD", 4, 4, 0b0111, False)

    @property
    def fields(self):
        return (self.PHASE1_PERIOD,
                self.PHASE2_PERIOD,
                BitField("CONST", 8, 8, 0xd9, True),
                )


class SEGPinConfiguration(LongRegister):
    ALT_SEG = BitField("ALT_SEG", 1, 4, 0b1, False)
    SEG_LEFT_RIGHT = BitField("SEG_LEFT_RIGHT", 1, 5, 0b0, False)

    @property
    def fields(self):
        return (BitField("CONST", 4, 0, 0b0000, True),
                self.ALT_SEG,
                BitField("CONST", 2, 6, 0b00, True),
                self.SEG_LEFT_RIGHT,
                BitField("CONST", 8, 8, 0xd9, True),
                )


class VCOMHDeselectLevel(LongRegister):
    VCOMH_DSEL = BitField("VCOMH_DSEL", 3, 4, 0b010, False)

    @property
    def fields(self):
        return (BitField("CONST", 4, 0, 0b0000, True),
                self.VCOMH_DSEL,
                BitField("CONST", 1, 7, 0b0, True),
                BitField("CONST", 8, 8, 0xd9, True),
                )


class FunctionSelectC(LongRegister):
    A10 = BitField("A10", 2, 0, 0b00, False)
    A7 = BitField("A7", 1, 7, 0b0, False)

    @property
    def fields(self):
        return (self.A10,
                BitField("CONST", 5, 2, 0b00000, True),
                self.A7,
                BitField("CONST", 8, 8, 0xdc, True),
                )


class FadeOutBlinkingConfig(LongRegister):
    VCOMH_DSEL = BitField("VCOMH_DSEL", 3, 4, 0b010, False)

    @property
    def fields(self):
        return (BitField("CONST", 4, 0, 0b0000, True),
                self.VCOMH_DSEL,
                BitField("CONST", 1, 7, 0b0, True),
                BitField("CONST", 8, 8, 0x23, True),
                )


class SO1602Instructions(HD44780Instructions):
    DataCommandSelect = DataCommandSelect()
    DisplayStatusExtra = DisplayStatusExtra()
    Function = Function()
    FunctionExtra = FunctionExtra()
    EntryModeExtra = EntryModeExtra()
    DoubleHeightShiftScroll = DoubleHeightShiftScroll()
    ScrollQuantity = ScrollQuantity()
    ShiftEnable = ShiftEnable()
    ScrollEnable = ScrollEnable()
    OLEDModeEntry = OLEDModeEntry()
    ContrastControl = ContrastControl()
    ClockControl = ClockControl()
    FunctionSelectA = FunctionSelectA()
    FunctionSelectB = FunctionSelectB()
    PhaseLength = PhaseLength()
    SEGPinConfiguration = SEGPinConfiguration()
    VCOMHDeselectLevel = VCOMHDeselectLevel()
    FunctionSelectC = FunctionSelectC()
    FadeOutBlinkingConfig = FadeOutBlinkingConfig()


class SO1602OLED(AQM0802):
    slave_address = SO1602A_ADDR
    instructions = SO1602Instructions()
    line_counter_const = 1

    def _startup(self):
        self.send_command(self.instructions.ClearDisplay.val)

        self.instructions.DisplayStatus.DISPLAY_ENABLE.val = 1
        self.instructions.DisplayStatus.CURSOR_ENABLE.val = 1
        self.instructions.DisplayStatus.CURSOR_BLINK_ENABLE.val = 1
        self.send_command(self.instructions.DisplayStatus.val)

        self.send_command(self.instructions.ReturnHome.val)

        self.send_command(self.instructions.FunctionExtra.val)  # RE=1

        self.instructions.DisplayStatusExtra.DISPLAY_LINES_NUMBER_MSB.val = 1
        self.send_command(self.instructions.DisplayStatusExtra.val)

        self.instructions.Function.DISPLAY_LINES_NUMBER_LSB.val = 1
        self.send_command(self.instructions.Function.val)

    def set_backlight(self, duty=50):
        max_duty = 255
        duty = min(max_duty, int(duty * max_duty / 100))

        self.send_command(self.instructions.FunctionExtra.val)

        self.instructions.OLEDModeEntry.OLED_COMMANDSET_ENABLE.val = 1
        self.send_command(self.instructions.OLEDModeEntry.val)

        self.send_command(self.instructions.ContrastControl.high_byte())
        self.instructions.ContrastControl.CONTRAST.val = duty
        self.send_command(self.instructions.ContrastControl.low_byte())

        self.instructions.OLEDModeEntry.OLED_COMMANDSET_ENABLE.val = 0
        self.send_command(self.instructions.OLEDModeEntry.val)

        self.send_command(self.instructions.Function.val)
