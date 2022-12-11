import hd44780compat
import AQM0802

SO1602A_ADDR = 0x3c  # 7-bit address


class SO1602OLED(AQM0802.AQM0802):
    slave_address = SO1602A_ADDR
    instructions = hd44780compat.HD44780Instructions()

    def _startup(self):
        self.send_command(self.instructions.ClearDisplay.val)

        self.instructions.DisplayStatus.DISPLAY_STATUS.val = 1
        self.instructions.DisplayStatus.CURSOR_STATUS.val = 1
        self.instructions.DisplayStatus.CURSOR_BLINK.val = 1
        self.send_command(self.instructions.DisplayStatus.val)

        self.send_command(self.instructions.ReturnHome.val)
