from collections import namedtuple


class BitField(namedtuple("BitField", ["name", "size", "offset", "por", "const"])):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__val = self.por

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

    def __init__(self):
        self.__val = self.por

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


class EntryMode(Register):
    """**Entry Mode Set (IS= X, RE = 0 or 1, SD = 0)**

    Set the moving direction of cursor and display.

    - ``I/D``: Increment/decrement of DDRAM address (cursor or blink)
        * When ``I/D`` = "High", cursor/blink moves to right and DDRAM address is increased by 1.
        * When ``I/D`` = "Low", cursor/blink moves to left and DDRAM address is decreased by 1.
    -   CGRAM operates the same as DDRAM, when read from or write to CGRAM.
    -   When ``S`` = "High", after DDRAM write, the display of enabled line by ``DS1`` - ``DS4`` bits in the command
        “Shift Enable” is shifted to the right (``I/D`` = "0") or to the left (``I/D`` = "1").
        But it will seem as if the cursor does not move.
    -   When ``S`` = "Low", or DDRAM read, or CGRAM read/write operation, shift of display like this function
        is not performed.
    """
    DISPLAY_SHIFT = BitField("DISPLAY_SHIFT", 1, 0, 0b0, False)
    INCREMENT_DECREMENT = BitField("INCREMENT_DECREMENT", 1, 1, 0b1, False)

    @property
    def fields(self):
        return (self.DISPLAY_SHIFT,
                self.INCREMENT_DECREMENT,
                BitField("CONST", 6, 2, 0b000001, True)
                )


class DisplayStatus(Register):
    """**Display ON/OFF Control (IS= X, RE = 0, SD = 0)**
    """
    CURSOR_BLINK_ENABLE = BitField("CURSOR_BLINK_ENABLE", 1, 0, 0b0, False)
    CURSOR_ENABLE = BitField("CURSOR_ENABLE", 1, 1, 0b0, False)
    DISPLAY_ENABLE = BitField("DISPLAY_ENABLE", 1, 2, 0b0, False)

    @property
    def fields(self):
        return (self.CURSOR_BLINK_ENABLE,
                self.CURSOR_ENABLE,
                self.DISPLAY_ENABLE,
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
    ClearDisplay = BitField("CLS", 8, 0, 0b0000_0001, True)
    """Clear all the display data by writing "20H" (space code) to all DDRAM address, and set DDRAM address to "00H" 
    into AC (address counter). Return cursor to the original status, namely, bring the cursor to the left edge on first 
    line of the display. Make entry mode increment (I/D = "1"). """

    ReturnHome = BitField("RTH", 8, 0, 0b0000_0010, True)
    """Return Home is cursor return home instruction. Set DDRAM address to "00H" into the address counter. 
    Return cursor to its original site and return display to its original status, if shifted. Contents of DDRAM 
    do not change. """

    EntryMode = EntryMode()
    DisplayStatus = DisplayStatus()
    Function = Function()
    DDRamAddress = DDRamAddress()
    DisplayShift = DisplayShift()
    CGRamAddress = CGRamAddress()


class CGFont(Register):
    size = 64
    CGRamAddress = CGRamAddress()
    Font0 = BitField("FONT", 8, 0, 0b00000, False)
    Font1 = BitField("FONT", 8, 8, 0b00000, False)
    Font2 = BitField("FONT", 8, 16, 0b00000, False)
    Font3 = BitField("FONT", 8, 24, 0b00000, False)
    Font4 = BitField("FONT", 8, 32, 0b00000, False)
    Font5 = BitField("FONT", 8, 40, 0b00000, False)
    Font6 = BitField("FONT", 8, 48, 0b00000, False)
    Font7 = BitField("FONT", 8, 56, 0b00000, False)

    def __init__(self, font_id, font_data):
        """
        :param int font_id: font id 0-7
        :param list of int font_data: font data, 8 bytes
        """
        super().__init__()

        assert len(font_data) == 8
        assert isinstance(font_id, int)

        mask = 0b111

        self.CGRamAddress.AC.val = (font_id & mask) << 3

        for field, font in zip(self.fields, font_data):
            field.val = font

    @property
    def fields(self):
        return (self.Font0,
                self.Font1,
                self.Font2,
                self.Font3,
                self.Font4,
                self.Font5,
                self.Font6,
                self.Font7,
                )
