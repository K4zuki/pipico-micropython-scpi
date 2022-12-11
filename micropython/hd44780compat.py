from collections import namedtuple


class BitField(namedtuple("BitField", ["name", "size", "offset", "por", "const"])):
    __val = 0

    @property
    def val(self):
        if self.const is True:
            return self.por
        else:
            return self.__val

    @val.setter
    def val(self, value):
        if self.const:
            pass
        else:
            mask = (1 << self.size) - 1
            self.__val = value & mask


class Register:
    size = 8
    __val = 0

    @property
    def fields(self):
        return (BitField("BIT_FIELD", 8, 0, 0xAA, False),
                )

    @property
    def por(self):
        val = 0
        for field in self.fields:
            val = val | (field.por << field.offset)
        val &= ((1 << self.size) - 1)
        return val

    @property
    def val(self):
        _val = 0
        for field in self.fields:
            _val = _val | (field.val << field.offset)
        return _val & ((1 << self.size) - 1)

    @val.setter
    def val(self, value):
        value = value & ((1 << self.size) - 1)
        for field in self.fields:
            mask = (1 << field.size) - 1
            field.val = (value >> field.offset) & mask


ClearDisplay = BitField("CLS", 8, 0, 0b0000_0001, True)
ReturnHome = BitField("RTH", 8, 0, 0b0000_0010, True)


class EntryMode(Register):
    DISPLAY_SHIFT = BitField("DISPLAY_SHIFT", 1, 0, 0b0, False)
    INCREMENT_DECREMENT = BitField("INCREMENT_DECREMENT", 1, 1, 0b1, False)

    @property
    def fields(self):
        return (self.DISPLAY_SHIFT,
                self.INCREMENT_DECREMENT,
                BitField("CONST", 6, 2, 0b000001, True)
                )


class DisplayStatus(Register):
    CURSOR_BLINK = BitField("CURSOR_BLINK", 1, 0, 0b0, False)
    CURSOR_STATUS = BitField("CURSOR_STATUS", 1, 1, 0b0, False)
    DISPLAY_STATUS = BitField("DISPLAY_STATUS", 1, 2, 0b0, False)

    @property
    def fields(self):
        return (self.CURSOR_BLINK,
                self.CURSOR_STATUS,
                self.DISPLAY_STATUS,
                BitField("CONST", 5, 3, 0b00001, True)
                )


class Function(Register):
    FONT_SELECTION = BitField("FONT_SELECTION", 1, 2, 0b0, False)
    DISPLAY_LINES_NUMBER = BitField("DISPLAY_LINES_NUMBER", 1, 3, 0b0, False)
    DATA_LENGTH = BitField("DATA_LENGTH", 1, 4, 0b0, False)

    @property
    def fields(self):
        return (BitField("CONST", 2, 0, 0b00, True),
                self.FONT_SELECTION,
                self.DISPLAY_LINES_NUMBER,
                self.DATA_LENGTH,
                BitField("CONST", 3, 5, 0b001, True),
                )


class DDRamAddress(Register):
    AC = BitField("AC", 7, 0, 0b0000000, False)

    @property
    def fields(self):
        return (self.AC,
                BitField("CONST", 1, 7, 0b1, True)
                )


class DisplayShift(Register):
    RIGHT_LEFT = BitField("RIGHT_LEFT", 1, 2, 0b0, False)
    SCREEN_CURSOR = BitField("SCREEN_CURSOR", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (BitField("CONST", 2, 0, 0b00, True),
                self.RIGHT_LEFT,
                self.SCREEN_CURSOR,
                BitField("CONST", 4, 4, 0b0001, True)
                )


class CGRamAddress(Register):
    AC = BitField("AC", 6, 0, 0b0000000, False)

    @property
    def fields(self):
        return (self.AC,
                BitField("CONST", 2, 6, 0b01, True)
                )


class HD44780Instructions:
    ClearDisplay = ClearDisplay
    ReturnHome = ReturnHome
    EntryMode = EntryMode()
    DisplayStatus = DisplayStatus()
    Function = Function()
    DDRamAddress = DDRamAddress()
    DisplayShift = DisplayShift()
    CGRamAddress = CGRamAddress()
