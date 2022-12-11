from hd44780compat import BitField, Register, HD44780Instructions
import AQM0802

SO1602A_ADDR = 0x3c  # 7-bit address


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
    REV = BitField("REV", 1, 0, 0b0, False)
    BE = BitField("BE", 1, 2, 0b0, False)
    DISPLAY_LINES_NUMBER_LSB = BitField("DISPLAY_LINES_NUMBER_LSB", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (self.REV,
                BitField("RE1", 1, 1, 0b1, True),
                self.BE,
                self.DISPLAY_LINES_NUMBER_LSB,
                BitField("CONST", 4, 4, 0b0010, True),
                )


class EntryModeExtra(Register):
    BDS = BitField("BDS", 1, 0, 0b0, False)
    BDC = BitField("BDC", 1, 1, 0b0, False)

    @property
    def fields(self):
        return (self.BDS,
                self.BDC,
                BitField("CONST", 6, 2, 0b000001, True),
                )


class OLEDModeEntry(Register):
    SD = BitField("SD", 1, 0, 0b0, False)

    @property
    def fields(self):
        return (self.SD,
                BitField("CONST", 7, 1, 0b0111_100, True),
                )


class SO1602Instructions(HD44780Instructions):
    DisplayStatusExtra = DisplayStatusExtra()
    Function = Function()
    EntryModeExtra = EntryModeExtra()
    FunctionExtra = FunctionExtra()
    OLEDModeEntry = OLEDModeEntry()
    ContrastControlMSB = BitField("ContrastControlMSB", 8, 0, 0x81, True)
    ContrastControlLSB = BitField("ContrastControlLSB", 8, 0, 0x7f, False)


class SO1602OLED(AQM0802.AQM0802):
    slave_address = SO1602A_ADDR
    instructions = SO1602Instructions()
    line_counter_const = 1

    def _startup(self):
        self.send_command(self.instructions.ClearDisplay.val)

        self.instructions.DisplayStatus.DISPLAY_STATUS.val = 1
        self.instructions.DisplayStatus.CURSOR_STATUS.val = 1
        self.instructions.DisplayStatus.CURSOR_BLINK.val = 1
        self.send_command(self.instructions.DisplayStatus.val)

        self.send_command(self.instructions.ReturnHome.val)

        self.instructions.Function.DISPLAY_LINES_NUMBER_LSB.val = 1
        self.send_command(self.instructions.Function.val)

        self.instructions.FunctionExtra.REV.val = 1
        self.instructions.FunctionExtra.DISPLAY_LINES_NUMBER_LSB.val = 1
        self.send_command(self.instructions.FunctionExtra.val)
        self.send_command(self.instructions.FunctionExtra.val)

        self.instructions.DisplayStatusExtra.FONT_WIDTH.val = 0
        self.send_command(self.instructions.FunctionExtra.val)
        self.send_command(self.instructions.DisplayStatusExtra.val)

        self.send_command(self.instructions.FunctionExtra.val)
        self.send_command(self.instructions.Function.val)

    def set_backlight(self, duty=50):
        max_duty = 255
        duty = min(max_duty, int(duty * max_duty / 100))  # avoid blackout when set at 100% duty

        self.send_command(self.instructions.FunctionExtra.val)

        self.instructions.OLEDModeEntry.SD.val = 1
        self.send_command(self.instructions.OLEDModeEntry.val)

        self.send_command(self.instructions.ContrastControlMSB.val)
        self.instructions.ContrastControlLSB.val = duty
        self.send_command(self.instructions.ContrastControlLSB.val)

        self.instructions.OLEDModeEntry.SD.val = 0
        self.send_command(self.instructions.OLEDModeEntry.val)

        self.send_command(self.instructions.Function.val)
