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

- PIN[6|7|14|15|20|21|22|25]:MODE[?] INput|OUTput|ODrain
- PIN[6|7|14|15|20|21|22|25]:VALue[?] 0|1|OFF|ON
- PIN[6|7|14|15|20|21|22|25]:ON
- PIN[6|7|14|15|20|21|22|25]:OFF
- PIN[6|7|14|15|20|21|22|25]:PWM:FREQuency[?] num
- PIN[6|7|14|15|20|21|22|25]:PWM:DUTY[?] num

- LED:ON
- LED:OFF
- LED:VALue[?] 0|1|OFF|ON
- LED:PWM:ENable
- LED:PWM:DISable
- LED:PWM:FREQuency[?] num
- LED:PWM:DUTY[?] num

- I2C[01]:SCAN?
- I2C[01]:FREQuency[?] num
- I2C[01]:ADDRess:BIT[?] 0|1|DEFault
- I2C[01]:WRITE address,buffer,stop
- I2C[01]:READ address,length,stop
- I2C[01]:MEMory:WRITE address,memaddress,buffer,addrsize
- I2C[01]:MEMory:READ address,memaddress,nbytes,addrsize

- SPI[01]:CSEL:POLarity[?] 0/1
- SPI[01]:MODE[?] 0/1/2/3
- SPI[01]:FREQuency[?] num
- SPI[01]:TRANSfer length,data

- ADC[0123]:READ?

"""
import sys
import re

import machine
from collections import namedtuple
from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice, cb_do_nothing

ABS_MAX_CLOCK = 275_000_000
ABS_MIN_CLOCK = 100_000_000
MAX_PWM_CLOCK = 100_000
MIN_PWM_CLOCK = 1_000
MAX_PWM_DUTY = 65536
MIN_PWM_DUTY = 0
MAX_I2C_CLOCK = 400_000
MIN_I2C_CLOCK = 10_000
MAX_SPI_CLOCK = 10_000_000
MIN_SPI_CLOCK = 10_000
MAX_UART_BAUD = 500_000
MIN_UART_BAUD = 300
IO_ON = 1
IO_OFF = 0
DEFAULT_I2C_BIT = 1

uart0 = machine.UART(0, tx=machine.Pin(0), rx=machine.Pin(1))
spi0 = machine.SPI(0, sck=machine.Pin(2), mosi=machine.Pin(3), miso=machine.Pin(4))
cs0 = machine.Pin(5, mode=machine.Pin.OUT, value=IO_ON)
pin6 = machine.Pin(6, machine.Pin.IN)
pin7 = machine.Pin(7, machine.Pin.IN)
uart1 = machine.UART(1, tx=machine.Pin(8), rx=machine.Pin(9))
spi1 = machine.SPI(1, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(12))
cs1 = machine.Pin(13, mode=machine.Pin.OUT, value=IO_ON)
pin14 = machine.Pin(14, machine.Pin.IN)
pin15 = machine.Pin(15, machine.Pin.IN)
sda0 = machine.Pin(16)
scl0 = machine.Pin(17)
i2c0 = machine.I2C(0, scl=scl0, sda=sda0)
sda1 = machine.Pin(18)
scl1 = machine.Pin(19)
i2c1 = machine.I2C(1, scl=scl1, sda=sda1)
pin20 = machine.Pin(20, machine.Pin.IN)
pin21 = machine.Pin(21, machine.Pin.IN)
pin22 = machine.Pin(22, machine.Pin.IN)
pin25 = machine.Pin(25, machine.Pin.OUT, value=IO_OFF)
adc0 = machine.ADC(machine.Pin(26))
adc1 = machine.ADC(machine.Pin(27))
adc2 = machine.ADC(machine.Pin(28))
adc3 = machine.ADC(machine.Pin(29))


class PinConfig(namedtuple("PinConfig", ["mode", "value", "pull"])):
    """
    mode: Pin.IN|OUT|OPEN_DRAIN|ALT
    value: 1/0
    pull: Pin.PULL_UP|PULL_DOWN
    """


class PwmConfig(namedtuple("PwmConfig", ["freq", "duty_u16"])):
    """
    :int freq: frequency
    :int duty_u16: duty
    """


class I2cConfig(namedtuple("I2cConfig", ["freq", "bit", "scl", "sda"])):
    """
    :int freq: frequency
    :int bit: addres bit
    :Pin scl: scl pin
    :Pin sda: sda pin
    """


class RaspberryScpiPico(MicroScpiDevice):
    kw_machine = ScpiKeyword("MACHINE", "MACHINE", None)
    kw_pin = ScpiKeyword("PIN", "PIN", ["6", "7", "14", "15", "20", "21", "22", "25"])
    kw_in = ScpiKeyword("INput", "IN", None)
    kw_out = ScpiKeyword("OUTput", "OUT", None)
    kw_od = ScpiKeyword("ODrain", "OD", None)
    kw_led = ScpiKeyword("LED", "LED", None)
    kw_status = ScpiKeyword("STATe", "STAT", ["?"])
    kw_pwm = ScpiKeyword("PWM", "PWM", None)
    kw_en = ScpiKeyword("ENable", "EN", None)
    kw_dis = ScpiKeyword("DISable", "DIS", None)
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
    kw_memory = ScpiKeyword("MEMory", "MEM", None)
    kw_freq = ScpiKeyword("FREQuency", "FREQ", ["?"])
    kw_spi = ScpiKeyword("SPI", "SPI", ["0", "1"])
    kw_csel = ScpiKeyword("CSEL", "CS", None)
    kw_mode = ScpiKeyword("MODE", "MODE", ["?"])
    kw_pol = ScpiKeyword("POLarity", "POL", ["?"])
    kw_xfer = ScpiKeyword("TRANSfer", "TRANS", None)
    kw_adc = ScpiKeyword("ADC", "ADC", ["0", "1", "2", "3"])
    kw_high = ScpiKeyword("HIGH", "HIGH", None)
    kw_low = ScpiKeyword("LOW", "LOW", None)
    kw_write = ScpiKeyword("WRITE", "WRITE", None)
    kw_read = ScpiKeyword("READ", "READ", ["?"])
    kw_value = ScpiKeyword("VALue", "VAL", ["?"])
    kw_def = ScpiKeyword("DEFault", "DEF", None)

    "PIN[6|7|14|15|20|21|22|25"
    pins = {
        6: pin6,
        7: pin7,
        14: pin14,
        15: pin15,
        20: pin20,
        21: pin21,
        22: pin22,
        25: pin25
    }
    i2c = {
        0: i2c0,
        1: i2c1
    }
    adc = {
        0: adc0,
        1: adc1,
        2: adc2,
        3: adc3
    }
    pin_conf = {
        6: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        7: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        14: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        15: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        20: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        21: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        22: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        25: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN)
    }
    pwm_conf = {
        6: PwmConfig(1000, 32768),
        7: PwmConfig(1000, 32768),
        14: PwmConfig(1000, 32768),
        15: PwmConfig(1000, 32768),
        20: PwmConfig(1000, 32768),
        21: PwmConfig(1000, 32768),
        22: PwmConfig(1000, 32768),
        25: PwmConfig(1000, 32768)
    }
    i2c_conf = {
        0: I2cConfig(100_000, 1, scl0, sda0),
        1: I2cConfig(100_000, 1, scl1, sda1)
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
        pin_pwm_freq = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_freq), False, self.cb_pin_pwm_freq)
        pin_pwm_duty = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_duty), False, self.cb_pin_pwm_duty)

        led_val = ScpiCommand((self.kw_led, self.kw_value), True, self.cb_led_val)
        led_on = ScpiCommand((self.kw_led, self.kw_on), False, self.cb_led_on)
        led_off = ScpiCommand((self.kw_led, self.kw_off), False, self.cb_led_off)
        led_pwm_freq = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_freq), False, self.cb_led_pwm_freq)
        led_pwm_duty = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_duty), False, self.cb_led_pwm_duty)

        i2c_scan_q = ScpiCommand((self.kw_i2c, self.kw_scan), True, self.cb_i2c_scan)
        i2c_freq = ScpiCommand((self.kw_i2c, self.kw_freq), False, self.cb_i2c_freq)
        i2c_abit = ScpiCommand((self.kw_i2c, self.kw_addr, self.kw_bit), False, self.cb_i2c_address_bit)
        i2c_write = ScpiCommand((self.kw_i2c, self.kw_write), False, self.cb_i2c_write)
        i2c_read_q = ScpiCommand((self.kw_i2c, self.kw_read), True, self.cb_i2c_read)
        i2c_write_memory = ScpiCommand((self.kw_i2c, self.kw_write, self.kw_memory), False, self.cb_i2c_write_memory)
        i2c_read_memory = ScpiCommand((self.kw_i2c, self.kw_read, self.kw_memory), True, self.cb_i2c_read_memory)

        spi_cpol = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_pol), False, cb_do_nothing)
        spi_mode = ScpiCommand((self.kw_spi, self.kw_mode), False, cb_do_nothing)
        spi_freq = ScpiCommand((self.kw_spi, self.kw_freq), False, cb_do_nothing)

        adc_read = ScpiCommand((self.kw_adc, self.kw_read), True, self.cb_adc_read)

        self.commands = [cls, ese, opc, rst, sre, esr_q, idn_q, stb_q, tst_q,
                         machine_freq,
                         pin_mode, pin_val, pin_on, pin_off, pin_pwm_freq, pin_pwm_duty,
                         led_val, led_on, led_off, led_pwm_freq, led_pwm_duty,
                         i2c_scan_q, i2c_freq, i2c_abit, i2c_write, i2c_read_q,
                         i2c_write_memory, i2c_read_memory,
                         spi_cpol, spi_mode, spi_freq,
                         adc_read,
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
        - PIN[6|7|14|15|20|21|22|25]:VALue[?] 0|1|OFF|ON

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        query = (opt[-1] == "?")
        conf = self.pin_conf[pin_number]

        if query:
            print("cb_pin_val", pin_number, "Query", param)
            val = pin.value()
            print(val)
        elif param is not None:
            print("cb_pin_val", pin_number, param)
            if param == str(IO_ON) or self.kw_on.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_ON)
                conf = PinConfig(machine.Pin.OUT, IO_ON, conf.pull)
                self.pin_conf[pin_number] = conf
            elif param == str(IO_OFF) or self.kw_off.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_OFF)
                conf = PinConfig(machine.Pin.OUT, IO_OFF, conf.pull)
                self.pin_conf[pin_number] = conf
            else:
                print("syntax error: invalid value:", param)
        else:
            print("syntax error: no parameter")

    def cb_pin_mode(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22|25]:MODE INput|OUTput|ODrain

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        query = (opt[-1] == "?")
        conf = self.pin_conf[pin_number]
        mode = conf.mode
        alt = 0

        if query:
            print("cb_pin_mode", pin_number, "Query", param)
            print(conf.mode)
        elif param is not None:
            print("cb_pin_mode", pin_number, param)
            if self.kw_in.match(param).match:
                mode = machine.Pin.IN
            elif self.kw_out.match(param).match:
                mode = machine.Pin.OUT
            elif self.kw_od.match(param).match:
                mode = machine.Pin.OPEN_DRAIN
            elif self.kw_pwm.match(param).match:
                mode = machine.Pin.ALT
                alt = machine.Pin.ALT_PWM
            else:
                print("syntax error: invalid value:", param)

            pin.init(mode, alt=alt, pull=conf.pull)
            self.pins[pin_number] = pin
            self.pin_conf[pin_number] = PinConfig(mode, conf.value, conf.pull)
            print(pin)
        else:
            print("syntax error: no parameter")

    def cb_pin_on(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22|25]:ON
        - PIN[6|7|14|15|20|21|22|25]:OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_on", pin_number, "Query", param)
        else:
            print("cb_pin_on", pin_number, param)
            self.cb_pin_val(param="ON", opt=opt)

    def cb_pin_off(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22|25]:ON
        - PIN[6|7|14|15|20|21|22|25]:OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        query = (opt[-1] == "?")

        if query:
            print("cb_pin_off", pin_number, "Query", param)
        else:
            print("cb_pin_off", pin_number, param)
            self.cb_pin_val(param="OFF", opt=opt)

    def cb_pin_pwm_freq(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:PWM:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        conf = self.pwm_conf[pin_number]
        query = (opt[-1] == "?")
        pwm_freq = param

        if query:
            print("cb_pin_pwm_freq", pin_number, "Query", param)
            pwm_freq = conf.freq
            print(f"{pwm_freq}")
        elif pwm_freq is not None:
            print("cb_pin_pwm_freq", pin_number, param)

            pwm_freq = int(float(pwm_freq))

            if MIN_PWM_CLOCK <= pwm_freq <= MAX_PWM_CLOCK:
                pwm = machine.PWM(pin)
                pwm.freq(conf.freq)
                pwm.duty_u16(conf.duty_u16)
                print(pwm)
                self.pwm_conf[pin_number] = PwmConfig(pwm_freq, conf.duty_u16)
            else:
                print("syntax error: out of range")
        else:
            print("syntax error: no parameter")

    def cb_pin_pwm_duty(self, param="", opt=None):
        """
        - PIN[6|7|14|15|20|21|22]:PWM:DUTY[?] num

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        conf = self.pwm_conf[pin_number]
        query = (opt[-1] == "?")
        pwm_duty = param

        if query:
            print("cb_pin_pwm_duty", pin_number, "Query", param)
            pwm_duty = conf.duty_u16
            print(f"{pwm_duty}")
        elif pwm_duty is not None:
            print("cb_pin_pwm_duty", pin_number, param)

            pwm_duty = int(float(pwm_duty))

            if MIN_PWM_DUTY <= pwm_duty <= MAX_PWM_DUTY:
                pwm = machine.PWM(pin)
                pwm.freq(conf.freq)
                pwm.duty_u16(conf.duty_u16)
                print(pwm)
                self.pwm_conf[pin_number] = PwmConfig(conf.freq, pwm_duty)
            else:
                print("syntax error: out of range")
        else:
            print("syntax error: no parameter")

    def cb_led_on(self, param="", opt=None):
        """
        - LED:ON

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")

        if query:
            print("cb_led_on", "Query", param)
        else:
            print("cb_led_on", param)
            self.cb_pin_val(param="ON", opt=opt)

    def cb_led_off(self, param="", opt=None):
        """
        - LED:OFF

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")

        if query:
            print("cb_led_off", "Query", param)
        else:
            print("cb_led_off", param)
            self.cb_pin_val(param="OFF", opt=opt)

    def cb_led_val(self, param, opt):
        """
        - LED:VALue 0|1|OFF|ON

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")

        if query:
            print("cb_led_state", "Query", param)
        elif param is not None:
            print("cb_led_state", param)
        else:
            print("syntax error: no parameter")

        self.cb_pin_val(param, opt)

    def cb_led_pwm_freq(self, param="", opt=None):
        """
        - LED:PWM:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")
        pwm_freq = param

        if query:
            print("cb_led_pwm_freq", "Query", param)
        elif pwm_freq is not None:
            print("cb_led_pwm_freq", param)
        else:
            print("syntax error: no parameter")

        self.cb_pin_pwm_freq(param, opt)

    def cb_led_pwm_duty(self, param, opt):
        """
        - LED:PWM:DUTY[?] num

        :param param:
        :param List[str] opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")
        pwm_duty = param

        if query:
            print("cb_pin_pwm_duty", "Query", param)
        elif pwm_duty is not None:
            print("cb_pin_pwm_duty", param)
        else:
            print("syntax error: no parameter")

        self.cb_pin_pwm_duty(param, opt)

    def cb_i2c_scan(self, param, opt):
        """
        - I2C[01]:SCAN?

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        conf = self.i2c_conf[bus_number]
        shift = conf.bit

        if query:
            print("cb_i2c_scan", "Query", param)
            scanned = bus.scan()
            if not scanned:
                print("0")
            else:
                print(",".join([s << shift for s in scanned]))
        else:
            print("syntax error: query only")

    def cb_i2c_freq(self, param, opt):
        """
        - I2C[01]:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        bus_freq = param
        conf = self.i2c_conf[bus_number]

        if query:
            print("cb_i2c_freq", bus_number, "Query", param)

            bus_freq = conf.freq
            print(f"{bus_freq}")
        elif bus_freq is not None:
            print("cb_i2c_freq", bus_number, param)

            bus_freq = int(float(bus_freq))

            if MIN_I2C_CLOCK <= bus_freq <= MAX_I2C_CLOCK:
                bus = machine.I2C(bus_number, scl=conf.scl, sda=conf.sda, freq=bus_freq)
                self.i2c[bus_number] = bus
                self.i2c_conf[bus_number] = I2cConfig(bus_freq, conf.bit, conf.scl, conf.sda)
            else:
                print("syntax error: out of range")
        else:
            print("syntax error: no parameter")

    def cb_i2c_address_bit(self, param, opt):
        """
        - I2C[01]:ADDRess:BIT[?] 0|1|DEFault

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        bit = param
        conf = self.i2c_conf[bus_number]

        if query:
            print("cb_i2c_address_bit", "Query", param)

            bit = conf.bit
            print(f"{bit}")
        elif bit is not None:
            print("cb_i2c_address_bit", param)
            if param in ["0", "1"]:
                self.i2c_conf[bus_number] = I2cConfig(conf.freq, int(param), conf.scl, conf.sda)
            elif self.kw_def.match(param):
                self.i2c_conf[bus_number] = I2cConfig(conf.freq, DEFAULT_I2C_BIT, conf.scl, conf.sda)
            else:
                print("syntax error: invalid value:", param)
        else:
            print("syntax error: no parameter")

    def cb_i2c_write(self, param, opt):
        """
        - I2C[01]:WRITE address,buffer,stop

        address: 01-ff
        buffer: data
        stop: 0|1

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        conf = self.i2c_conf[bus_number]
        shift = conf.bit

        if query:
            print("cb_i2c_write", "Query", param)
        elif param is not None:
            print("cb_i2c_write", param)
        else:
            print("syntax error: no parameter")

    def cb_i2c_read(self, param, opt):
        """
        - I2C[01]:READ address,length,stop

        address: 01-ff
        length: 1-99
        stop: 0|1

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        conf = self.i2c_conf[bus_number]
        shift = conf.bit
        rstring = re.compile(r"^([0-9a-fA-F][1-9a-fA-F]),([1-9][0-9]+),([01])$")

        if query:
            print("cb_i2c_read", "Query", param)
        elif param is not None:
            print("cb_i2c_read", param)

            searched = rstring.search(param)
            if searched is not None:
                address, length, stop = searched.groups()
                stop = True if (int(stop) == 1) else False
                address = int(f"0x{address}") >> shift
                print(f"0x{address:02x}", length, stop)
                try:
                    read = bus.readfrom(int(address), int(length), stop)
                    print(",".join([str(r) for r in read]))
                except OSError:
                    print("bus read failed")
        else:
            print("syntax error: no parameter")

    def cb_i2c_write_memory(self, param, opt):
        """
        - I2C[01]:MEMory:WRITE address,memaddress,buf,addrsize

        address: 01-ff
        memaddress: 0000-ffff
        buf: data
        addrsize: 1|2

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        conf = self.i2c_conf[bus_number]
        shift = conf.bit
        rstring = re.compile(r"^([0-9a-fA-F][1-9a-fA-F]),([0-9a-fA-F].|[0-9a-fA-F]...),([1-9][0-9]+),([01])$")

        if query:
            print("cb_i2c_write_memory", "Query", param)
        elif param is not None:
            print("cb_i2c_write_memory", param)

            searched = rstring.search(param)

            if searched is not None:
                address, memaddress, data, addrsize = searched.groups()

                address = int(f"0x{address}") >> shift
                memaddress = int(f"0x{memaddress}")
                data = bytes(data, encoding="utf-8")
                addrsize = 8 * int(addrsize)

                bus.writeto_mem(address, memaddress, data, addrsize)
            else:
                print("syntax error: invalid parameters")
        else:
            print("syntax error: no parameter")

    def cb_i2c_read_memory(self, param, opt):
        """
        - I2C[01]:MEMory:READ? address,memaddress,nbytes,addrsize

        addr: 01-FF
        memaddr: 00-FF | 0000-FFFF
        nbytes: 1-99
        addrsize: 1|2

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.i2c[bus_number]
        conf = self.i2c_conf[bus_number]
        shift = conf.bit
        rstring = re.compile(r"^([0-9a-fA-F][1-9a-fA-F]),([0-9a-fA-F].|[0-9a-fA-F]...),([1-9][0-9]+),([12])$")

        if query:
            print("cb_i2c_read_memory", "Query", param)

            if param is not None:
                searched = rstring.search(param)
                if searched is not None:
                    address, memaddress, length, addrsize = searched.groups()
                    address = int(f"0x{address}") >> shift
                    memaddress = int(f"0x{memaddress}")
                    length = int(f"0x{length}")
                    addrsize = 8 * int(addrsize)

                    data = bus.readfrom_mem(address, memaddress, length, addrsize)
                    print(data)
                else:
                    print("syntax error: invalid parameters")
            else:
                print("syntax error: no parameter")
        else:
            print("syntax error: query only")

    def cb_adc_read(self, param, opt):
        """
        - ADC[012]:READ?

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        adc_ch = int(opt[0])
        adc = self.adc[adc_ch]

        if query:
            print("cb_adc_read", "Query", param)
            value = adc.read_u16()
            print(f"{value}")  # decimal
        else:
            print("syntax error: query only")
