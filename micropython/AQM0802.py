from machine import I2C, Pin, PWM

AQM0802_ADDR = 0x3e  # 7-bits


class AQM0802:
    bus = None
    bled = None
    reset = None

    def __init__(self, bus, bled, reset=None):
        """

        :param I2C bus:
        :param PWM bled:
        :param Pin reset:
        """
        self.bus = bus
        self.bled = bled
        self.reset = reset

        if AQM0802_ADDR in self.bus.scan():
            self._init_lcd()

    def _init_lcd(self):
        self.send_command(0x38)
        self.send_command(0x39)
        self.send_command(0x14)
        self.send_command(0x70)
        self.send_command(0x56)
        self.send_command(0x6c)
        self.send_command(0x38)
        self.send_command(0x0c)
        self.send_command(0x01)
        self.set_backlight(50)

    def send_command(self, command):
        self.bus.writeto(AQM0802_ADDR, bytes([0x00, command]))
        return

    def send_data(self, data):
        self.bus.writeto(AQM0802_ADDR, bytes([0x40, data]))
        return

    def set_backlight(self, duty=50):
        max_duty = 65535
        if self.bled is not None:
            duty = min(max_duty, int(duty * 65536 // 100))
            self.bled.duty_u16(duty)
