from machine import I2C, Pin, PWM

from hd44780compat import BitField, Register, Function, HD44780Instructions, CGFont

CR = 0x0d
LF = 0x0a
AQM0802_ADDR = 0x3e  # 7-bits


class DataCommandSelect(Register):
    DATA_COMMAND = BitField("DATA_COMMAND", 1, 6, 0b0, False)
    CONTINUATION = BitField("CONTINUATION", 1, 7, 0b0, False)

    @property
    def fields(self):
        return (BitField("CONST", 6, 0, 0b00_0000, True),
                self.DATA_COMMAND,
                self.CONTINUATION
                )


class AQM0802Function(Function):
    INSTRUCTION_TABLE = BitField("INSTRUCTION_TABLE", 1, 0, 0b00, False)

    @property
    def fields(self):
        return (self.INSTRUCTION_TABLE,
                BitField("CONST", 1, 1, 0b0, True),
                self.FONT_SELECTION,
                self.DISPLAY_LINES_NUMBER,
                self.DATA_LENGTH,
                BitField("CONST", 3, 5, 0b001, True),
                )


class InternalOscillator(Register):
    ADJUST = BitField("ADJUST", 3, 0, 0b000, False)
    BIAS = BitField("BIAS", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (self.ADJUST,
                self.BIAS,
                BitField("CONST", 4, 4, 0b0001, True),
                )


class ICONAddress(Register):
    AC = BitField("AC", 4, 0, 0b0000, False)

    @property
    def fields(self):
        return (self.AC,
                BitField("CONST", 4, 4, 0b0100, True),
                )


class PowerControl(Register):
    CONTRAST_MSB = BitField("CONTRAST_MSB", 2, 0, 0b00, False)
    BOOST_STATUS = BitField("BOOST_STATUS", 1, 2, 0b0, False)
    ICON_STATUS = BitField("ICON_STATUS", 1, 3, 0b0, False)

    @property
    def fields(self):
        return (self.CONTRAST_MSB,
                self.BOOST_STATUS,
                self.ICON_STATUS,
                BitField("CONST", 4, 4, 0b0101, True),
                )


class FollowerControl(Register):
    FOLLOWER_STATUS = BitField("FOLLOWER_STATUS", 1, 3, 0b0, False)
    AMPL_RATIO = BitField("AMPL_RATIO", 3, 0, 0b000, False)

    @property
    def fields(self):
        return (self.AMPL_RATIO,
                self.FOLLOWER_STATUS,
                BitField("CONST", 4, 4, 0b0110, True),
                )


class ContrastSet(Register):
    CONTRAST_LSB = BitField("CONTRAST_LSB", 4, 0, 0b0000, False)

    @property
    def fields(self):
        return (self.CONTRAST_LSB,
                BitField("CONST", 4, 4, 0b0111, True),
                )


class AQM0802Instructions(HD44780Instructions):
    DataCommandSelect = DataCommandSelect()
    Function = AQM0802Function()
    InternalOscillator = InternalOscillator()
    ICONAddress = ICONAddress()
    PowerControl = PowerControl()
    FollowerControl = FollowerControl()
    ContrastSet = ContrastSet()


class AQM0802:
    slave_address = AQM0802_ADDR
    bus = None
    bled = None
    rst = None
    visible = False
    line_counter = 0x00
    line_counter_const = 2
    instructions = AQM0802Instructions()

    def __init__(self, bus, bled=None, reset=None):
        """

        :param I2C bus:
        :param PWM bled:
        :param Pin reset:
        """
        self.bus = bus
        self.bled = bled
        self.rst = reset

        if self.slave_address in self.bus.scan():
            self.visible = True
            self._startup()

        self.set_backlight(30)

    def _startup(self):
        self.instructions.Function.INSTRUCTION_TABLE.val = 0
        self.instructions.Function.DISPLAY_LINES_NUMBER.val = 1
        self.instructions.Function.DATA_LENGTH.val = 1
        self.send_command(self.instructions.Function.val)
        # self.send_command(0x38)

        self.instructions.Function.INSTRUCTION_TABLE.val = 1
        self.send_command(self.instructions.Function.val)
        # self.send_command(0x39)

        self.instructions.InternalOscillator.BIAS.val = 0
        self.instructions.InternalOscillator.ADJUST.val = 4
        self.send_command(self.instructions.InternalOscillator.val)
        # self.send_command(0x14)

        self.instructions.ContrastSet.CONTRAST_LSB.val = 0
        self.send_command(self.instructions.ContrastSet.val)
        # self.send_command(0x70)

        self.instructions.PowerControl.BOOST_STATUS.val = 1
        self.instructions.PowerControl.CONTRAST_MSB.val = 2
        self.send_command(self.instructions.PowerControl.val)
        # self.send_command(0x56)

        self.instructions.FollowerControl.FOLLOWER_STATUS.val = 1
        self.instructions.FollowerControl.AMPL_RATIO.val = 4
        self.send_command(self.instructions.FollowerControl.val)
        # self.send_command(0x6c)

        self.instructions.Function.INSTRUCTION_TABLE.val = 0
        self.send_command(self.instructions.Function.val)
        # self.send_command(0x38)

        self.instructions.DisplayStatus.DISPLAY_ENABLE.val = 1
        self.instructions.DisplayStatus.CURSOR_ENABLE.val = 1
        self.instructions.DisplayStatus.CURSOR_BLINK_ENABLE.val = 1
        self.send_command(self.instructions.DisplayStatus.val)
        # self.send_command(0x0c)

        self.send_command(self.instructions.ClearDisplay.val)
        # self.send_command(0x01)

    def reset(self):
        self.line_counter = 0x00
        if self.rst is not None:
            self.rst.off()
            self.rst.on()
        self._startup()

    def send_command(self, command):
        if self.visible:
            self.bus.writeto(self.slave_address, bytes([0x00, command]))
        return

    def send_data(self, data):
        if data == LF:
            self.line_feed()
            self.send_command(0x80 | (self.line_counter << 5))
        elif data == CR:
            pass
        else:
            if self.visible:
                self.bus.writeto(self.slave_address, bytes([0x40, data]))
        return

    def line_feed(self):
        self.line_counter += self.line_counter_const
        self.line_counter &= self.line_counter_const

    def set_backlight(self, duty=50):
        max_duty = 65535
        if self.bled is not None:
            duty = min(max_duty - 1, int(duty * max_duty / 100))  # avoid blackout when set at 100% duty
            self.bled.duty_u16(duty)

    def cls(self):
        self.send_command(self.instructions.ClearDisplay.val)
        self.line_counter = 0

    def send_font(self, font):
        """
        :param CGFont font:
        """
        cgaddress = font.CGRamAddress.val
        font_data = [b.val for b in font.fields]

        self.send_command(cgaddress)
        for data in font_data:
            self.send_data(data)
