"""
- *CLS <No Param>
- *ESE/*ESE? <No Param>
- *ESR? <No Param>
- *IDN? <No Param>
- *OPC/*OPC? <No Param>
- *RST <No Param>
- *SRE/*SRE? <No Param>
- *STB? <No Param>
- *TST? <No Param>

- MACHINE:FREQuency[?] num

- PIN[6|7|14|15|20|21|22]:MODE[?]
- PIN[6|7|14|15|20|21|22]:VALue[?]
- PIN[6|7|14|15|20|21|22]:ON
- PIN[6|7|14|15|20|21|22]:OFF
- PIN[6|7|14|15|20|21|22]:PWM:FREQuency[?] num
- PIN[6|7|14|15|20|21|22]:PWM:DUTY[?] num

- LED:ON
- LED:OFF
- LED:STATe[?] 0/1

- I2C:BUS[01]:SCAN?
- I2C:BUS[01]:FREQuency[?] num
- I2C:BUS[01]:ADDRess:BIT[?] 0/1
- I2C:BUS[01]:WRITE data,repeated
- I2C:BUS[01]:READ? address,length,repeated

- SPI:BUS[01]:CSEL:POLarity[?] 0/1
- SPI:BUS[01]:MODE[?] 0/1/2/3
- SPI:BUS[01]:FREQuency[?] num
- SPI:BUS[01]:TRANSfer length

- ADC[012]:READ?

"""
import sys

import machine
from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice, cb_do_nothing

ABS_MAX_CLOCK = 275_000_000
ABS_MIN_CLOCK = 100_000_000

uart0 = machine.UART(0, tx=machine.Pin(0), rx=machine.Pin(1))
spi0 = machine.SPI(0, sck=machine.Pin(2), mosi=machine.Pin(3), miso=machine.Pin(4))
cs0 = machine.Pin(5, mode=machine.Pin.OUT, value=1)
pin6 = machine.Pin(6, machine.Pin.IN)
pin7 = machine.Pin(7, machine.Pin.IN)
uart1 = machine.UART(1, tx=machine.Pin(8), rx=machine.Pin(9))
spi1 = machine.SPI(1, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
cs1 = machine.Pin(13, mode=machine.Pin.OUT, value=1)
pin14 = machine.Pin(14, machine.Pin.IN)
pin15 = machine.Pin(15, machine.Pin.IN)
i2c0 = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16))
i2c1 = machine.I2C(1, scl=machine.Pin(19), sda=machine.Pin(18))
pin20 = machine.Pin(20, machine.Pin.IN)
pin21 = machine.Pin(21, machine.Pin.IN)
pin22 = machine.Pin(22, machine.Pin.IN)
pin25 = machine.Pin(25, machine.Pin.OUT, value=0)
adc0 = machine.ADC(machine.Pin(26))
adc1 = machine.ADC(machine.Pin(27))
adc2 = machine.ADC(machine.Pin(28))


class RaspberryScpiPico(MicroScpiDevice):
    kw_cls = ScpiKeyword("*CLS", "*CLS", None)
    kw_ese = ScpiKeyword("*ESE", "*ESE", ["?"])
    kw_esr = ScpiKeyword("*ESR", "*ESR", ["?"])
    kw_idn = ScpiKeyword("*IDN", "*IDN", ["?"])
    kw_opc = ScpiKeyword("*OPC", "*OPC", ["?"])
    kw_rst = ScpiKeyword("*RST", "*RST", ["?"])
    kw_sre = ScpiKeyword("*SRE", "*SRE", ["?"])
    kw_stb = ScpiKeyword("*STB", "*STB", ["?"])
    kw_tst = ScpiKeyword("*TST", "*TST", ["?"])

    kw_machine = ScpiKeyword("MACHINE", "MACHINE", None)
    kw_pin = ScpiKeyword("PIN", "PIN", ["6", "7", "14", "15", "20", "21", "22"])
    kw_led = ScpiKeyword("LED", "LED", None)
    kw_status = ScpiKeyword("STATe", "STAT", ["?"])
    kw_pwm = ScpiKeyword("PWM", "PWM", None)
    kw_duty = ScpiKeyword("DUTY", "DUTY", ["?"])
    kw_on = ScpiKeyword("ON", "ON", None)
    kw_off = ScpiKeyword("OFF", "OFF", None)
    kw_uart = ScpiKeyword("UART", "UART", None)
    kw_baud = ScpiKeyword("BAUDrate", "BAUD", None)
    kw_parity = ScpiKeyword("PARITY", "PARITY", None)
    kw_width = ScpiKeyword("WIDTH", "WIDTH", None)
    kw_start = ScpiKeyword("START", "START", None)
    kw_stop = ScpiKeyword("STOP", "STOP", None)
    kw_i2c = ScpiKeyword("I2C", "I2C", ["0", "1"])
    kw_scan = ScpiKeyword("SCAN", "SCAN", ["?"])
    kw_addr = ScpiKeyword("ADDRess", "ADDR", None)
    kw_bit = ScpiKeyword("BIT", "BIT", ["?"])
    kw_freq = ScpiKeyword("FREQuency", "FREQ", ["?"])
    kw_spi = ScpiKeyword("SPI", "SPI", ["0", "1"])
    kw_csel = ScpiKeyword("CSEL", "CS", None)
    kw_mode = ScpiKeyword("MODE", "MODE", ["?"])
    kw_pol = ScpiKeyword("POLarity", "POL", ["?"])
    kw_xfer = ScpiKeyword("TRANSfer", "TRANS", None)
    kw_adc = ScpiKeyword("ADC", "ADC", ["0", "1", "2"])
    kw_high = ScpiKeyword("HIGH", "HIGH", None)
    kw_low = ScpiKeyword("LOW", "LOW", None)
    kw_write = ScpiKeyword("WRITE", "WRITE", None)
    kw_read = ScpiKeyword("READ", "READ", ["?"])
    kw_value = ScpiKeyword("VALue", "VAL", ["?"])

    "PIN[6|7|14|15|20|21|22]"
    pins = {
        6: pin6,
        7: pin7,
        14: pin14,
        15: pin15,
        20: pin20,
        21: pin21,
        22: pin22
    }

    def __init__(self):
        super().__init__()

        cls = ScpiCommand((self.kw_cls,), False, cb_do_nothing)
        ese = ScpiCommand((self.kw_ese,), False, cb_do_nothing)
        opc = ScpiCommand((self.kw_opc,), False, cb_do_nothing)
        rst = ScpiCommand((self.kw_rst,), False, cb_do_nothing)
        sre = ScpiCommand((self.kw_sre,), False, cb_do_nothing)
        esr_q = ScpiCommand((self.kw_esr,), True, cb_do_nothing)
        idn_q = ScpiCommand((self.kw_idn,), True, self.cb_idn)
        stb_q = ScpiCommand((self.kw_stb,), True, cb_do_nothing)
        tst_q = ScpiCommand((self.kw_tst,), True, cb_do_nothing)

        machine_freq = ScpiCommand((self.kw_machine, self.kw_freq), False, self.cb_machine_freq)

        pin_mode = ScpiCommand((self.kw_pin, self.kw_mode), False, self.cb_pin_mode)
        pin_val = ScpiCommand((self.kw_pin, self.kw_value), False, self.cb_pin_val)
        pin_on = ScpiCommand((self.kw_pin, self.kw_on), False, self.cb_pin_on)
        pin_off = ScpiCommand((self.kw_pin, self.kw_off), False, self.cb_pin_off)

        led_stat = ScpiCommand((self.kw_led, self.kw_status), True, self.cb_led_state)
        led_on = ScpiCommand((self.kw_led, self.kw_on), False, self.cb_led_on)
        led_off = ScpiCommand((self.kw_led, self.kw_off), False, self.cb_led_off)

        pwm_freq = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_freq), False, self.cb_pin_pwm_freq)
        pwm_duty = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_duty), False, self.cb_pin_pwm_duty)

        i2c_scan_q = ScpiCommand((self.kw_i2c, self.kw_scan), True, cb_do_nothing)
        i2c_freq = ScpiCommand((self.kw_i2c, self.kw_freq), False, cb_do_nothing)
        i2c_abit = ScpiCommand((self.kw_i2c, self.kw_addr, self.kw_bit), False, cb_do_nothing)
        i2c_write = ScpiCommand((self.kw_i2c, self.kw_write), False, cb_do_nothing)
        i2c_read_q = ScpiCommand((self.kw_i2c, self.kw_read), True, cb_do_nothing)

        spi_cpol = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_pol), False, cb_do_nothing)
        spi_mode = ScpiCommand((self.kw_spi, self.kw_mode), False, cb_do_nothing)
        spi_freq = ScpiCommand((self.kw_spi, self.kw_freq), False, cb_do_nothing)

        adc_read_q = ScpiCommand((self.kw_adc, self.kw_read), True, cb_do_nothing)

        self.commands = [cls, ese, opc, rst, sre, esr_q, idn_q, stb_q, tst_q,
                         machine_freq,
                         pin_mode, pin_val, pin_on, pin_off,
                         led_stat, led_on, led_off,
                         pwm_freq, pwm_duty,
                         i2c_scan_q, i2c_freq, i2c_abit, i2c_write, i2c_read_q,
                         spi_cpol, spi_mode, spi_freq,
                         adc_read_q,
                         ]

    @staticmethod
    def cb_idn(param="", opt=None):
        """<Vendor name>,<Model number>,<Serial number>,<Firmware version>"""
        serial = machine.unique_id()
        print(f"RaspberryPiPico,RP001,{serial},0.0.1")

    @staticmethod
    def cb_version(param="", opt=None):
        """The command returns a string in the form of “YYYY.V”, where “YYYY” represents
        the year of the version and “V” represents a version for that year (e.g. 1997.0).
        """
        print("2023.04")

    @staticmethod
    def cb_machine_freq(param="", opt=None):
        """

        :return:
        """

        machine_freq = param
        query = (opt[-1] == "?")

        print("cb_machine_freq", param, opt)
        if query:
            machine_freq = machine.freq()
            print(f"{machine_freq}")
        else:
            assert machine_freq is not None
            machine_freq = int(float(machine_freq))
            assert ABS_MIN_CLOCK < machine_freq < ABS_MAX_CLOCK
            assert isinstance(machine_freq, (int, float))
            machine.freq(machine_freq)

    def cb_pin_val(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:VALue[?]
        :param param:
        :param opt:
        :return:
        """

        pin_number = opt[0]
        pin = self.pins[int(pin_number)]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_val", pin_number, "Query", param)
            val = pin.value()
            print(val)
        else:
            print("cb_pin_val", pin_number, int(param))
            if int(param) in [0, 1]:
                pin.value(int(param))

    @staticmethod
    def cb_pin_mode(param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:MODE[?]

        :param param:
        :param opt:
        :return:
        """
        pin_number = opt[0]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_mode", pin_number, "Query", param)
        else:
            print("cb_pin_mode", pin_number, param)

    @staticmethod
    def cb_pin_on(param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:ON
        - PIN[6|7|14|15|20|21|22]:OFF

        :param param:
        :param opt:
        :return:
        """
        pin_number = opt[0]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_on", pin_number, "Query", param)
        else:
            print("cb_pin_on", pin_number, param)

    @staticmethod
    def cb_pin_off(param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:ON
        - PIN[6|7|14|15|20|21|22]:OFF

        :param param:
        :param opt:
        :return:
        """
        pin_number = opt[0]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_off", pin_number, "Query", param)
        else:
            print("cb_pin_off", pin_number, param)

    @staticmethod
    def cb_pin_pwm_freq(param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:PWM:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """
        pin_number = opt[0]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_pwm_freq", pin_number, "Query", param)
        else:
            print("cb_pin_pwm_freq", pin_number, param)

    @staticmethod
    def cb_pin_pwm_duty(param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:PWM:DUTY[?] num

        :param param:
        :param opt:
        :return:
        """
        pin_number = opt[0]
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_pwm_duty", pin_number, "Query", param)
        else:
            print("cb_pin_pwm_duty", pin_number, param)

    @staticmethod
    def cb_led_on(param="", opt=None):
        """
        - LED:ON

        :param param:
        :param opt:
        :return:
        """
        query = (opt[-1] == "?")

        if query:
            print("cb_led_on", "Query", param)
        else:
            print("cb_led_on", param)
            pin25.on()

    @staticmethod
    def cb_led_off(param="", opt=None):
        """
        - LED:OFF

        :param param:
        :param opt:
        :return:
        """
        query = (opt[-1] == "?")

        if query:
            print("cb_led_off", "Query", param)
        else:
            print("cb_led_off", param)
            pin25.off()

    @staticmethod
    def cb_led_state(param="", opt=None):
        """
        - LED:STATe 0|1

        :param param:
        :param opt:
        :return:
        """

        pin = pin25
        query = (opt[-1] == "?")

        if query:
            print("cb_led_state", "Query", param)
            val = pin.value()
            print(val)
        else:
            print("cb_led_state", int(param))
            if int(param) in [0, 1]:
                pin.value(int(param))
