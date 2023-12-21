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

- SYSTem:ERRor?

- PIN[6|7|14|15|20|21|22|25]?
- PIN[6|7|14|15|20|21|22|25]:MODE[?] INput|OUTput|ODrain|PWM
- PIN[6|7|14|15|20|21|22|25]:VALue[?] 0|1|OFF|ON
- PIN[6|7|14|15|20|21|22|25]:ON
- PIN[6|7|14|15|20|21|22|25]:OFF
- PIN[6|7|14|15|20|21|22|25]:PWM:FREQuency[?] num
- PIN[6|7|14|15|20|21|22|25]:PWM:DUTY[?] num

- LED?
- LED:ON
- LED:OFF
- LED:VALue[?] 0|1|OFF|ON
- LED:PWM:ENable
- LED:PWM:DISable
- LED:PWM:FREQuency[?] num
- LED:PWM:DUTY[?] num

- I2C?
- I2C[01]:SCAN?
- I2C[01]:FREQuency[?] num
- I2C[01]:ADDRess:BIT[?] 0|1|DEFault
- I2C[01]:WRITE address,buffer,stop
- I2C[01]:READ? address,length,stop
- I2C[01]:MEMory:WRITE address,memaddress,buffer,addrsize
- I2C[01]:MEMory:READ address,memaddress,nbytes,addrsize

- SPI?
- SPI[01]:CSEL:POLarity[?] 0|1|DEFault
- SPI[01]:CSEL:VALue[?] 0|1|OFF|ON
- SPI[01]:MODE[?] 0|1|2|3|DEFault
- SPI[01]:FREQuency[?] num
- SPI[01]:TRANSfer data,pre_cs,post_cs
- SPI[01]:WRITE data,pre_cs,post_cs
- SPI[01]:READ? length,mask,pre_cs,post_cs

- ADC[01234]:READ?

"""
import sys
import machine

import re
from math import ceil
from collections import namedtuple
from MicroScpiDevice import ScpiKeyword, ScpiCommand, ScpiErrorNumber, MicroScpiDevice, cb_do_nothing, ERROR_LIST

ABS_MAX_CLOCK = 275_000_000
DEFAULT_CPU_CLOCK = 125_000_000
ABS_MIN_CLOCK = 100_000_000
MAX_PWM_CLOCK = 100_000
MIN_PWM_CLOCK = 1_000
MAX_PWM_DUTY = 65535
MIN_PWM_DUTY = 0
MAX_I2C_CLOCK = 400_000
MIN_I2C_CLOCK = 10_000
MAX_SPI_CLOCK = 10_000_000
MIN_SPI_CLOCK = 10_000
MAX_UART_BAUD = 500_000
MIN_UART_BAUD = 300
IO_ON = 1
IO_OFF = 0
IO_VALUE_STRINGS = {IO_ON: "ON", IO_OFF: "OFF"}
IO_MODE_STRINGS = {machine.Pin.IN: "IN", machine.Pin.OUT: "OUT",
                   machine.Pin.OPEN_DRAIN: "ODrain", machine.Pin.ALT: "PWM"}
DEFAULT_I2C_BIT = 1
SPI_MODE0 = 0
SPI_MODE1 = 1
SPI_MODE2 = 2
SPI_MODE3 = 3
DEFAULT_SPI_MODE = SPI_MODE0
SPI_CSPOL_HI = 1
SPI_CSPOL_LO = 0
DEFAULT_SPI_CSPOL = SPI_CSPOL_LO
SPI_MASK_CKPOL = 0x02
SPI_CKPOL_HI = 1
SPI_CKPOL_LO = 0
DEFAULT_SPI_CKPOL = SPI_CKPOL_LO
SPI_MASK_CKPH = 0x01
SPI_CKPH_HI = 1
SPI_CKPH_LO = 0
DEFAULT_SPI_CKPH = SPI_CKPH_LO

"""
-102    syntax error; invalid syntax
-108    parameter not allowed; more parameters than expected
-109    missing parameter; fewer parameters than expected
-113    undefined header; invalid command received
-121    invalid character in number; parameter has invalid number character
-148    character data not allowed; discrete parameter was received while string or numeric was expected
-158    string data not allowed; unexpected string parameter received
-222    data out of range; data value was outside of valid range
-223    too much data; more data than expected
-224    illegal parameter value; invalid parameter choice
-333    I2C bus access fail
-334    SPI bus access fail
"""

BUS_FAIL_CODE = 0
E_NONE = ScpiErrorNumber(0, "No error")
E_SYNTAX = ScpiErrorNumber(-102, "Syntax error")
E_PARAM_UNALLOWED = ScpiErrorNumber(-108, "Parameter not allowed")
E_MISSING_PARAM = ScpiErrorNumber(-109, "Missing parameter")
E_UNDEFINED_HEADER = ScpiErrorNumber(-113, "Undefined header")
E_WRONG_NUMBER_CHARACTER = ScpiErrorNumber(-121, "Invalid character in number")
E_CHARACTER_UNALLOWED = ScpiErrorNumber(-148, "Character data not allowed")
E_STRING_UNALLOWED = ScpiErrorNumber(-158, "String data not allowed")
E_OUT_OF_RANGE = ScpiErrorNumber(-222, "Data out of range")
E_DATA_OVERFLOW = ScpiErrorNumber(-223, "Too much data")
E_INVALID_PARAMETER = ScpiErrorNumber(-224, "Illegal parameter value")
E_I2C_FAIL = ScpiErrorNumber(-333, "I2C bus error")
E_SPI_FAIL = ScpiErrorNumber(-334, "SPI bus error")

pin0 = machine.Pin(0)  # no-error indicator
pin1 = machine.Pin(1)  # error indicator

sck0 = machine.Pin(2)
mosi0 = machine.Pin(3)
miso0 = machine.Pin(4)
spi0 = machine.SPI(0, sck=sck0, mosi=mosi0, miso=miso0)
cs0 = machine.Pin(5, mode=machine.Pin.OUT, value=IO_ON)

sda1 = machine.Pin(6)
scl1 = machine.Pin(7)
i2c1 = machine.I2C(1, scl=scl1, sda=sda1)

sda0 = machine.Pin(8)
scl0 = machine.Pin(9)
i2c0 = machine.I2C(0, scl=scl0, sda=sda0)

sck1 = machine.Pin(10)
mosi1 = machine.Pin(11)
miso1 = machine.Pin(12)
spi1 = machine.SPI(1, sck=sck1, mosi=mosi1, miso=miso1)
cs1 = machine.Pin(13, mode=machine.Pin.OUT, value=IO_ON)

pin14 = machine.Pin(14, machine.Pin.IN)
pin15 = machine.Pin(15, machine.Pin.IN)
pin16 = machine.Pin(16, machine.Pin.IN)
pin17 = machine.Pin(17, machine.Pin.IN)
pin18 = machine.Pin(18, machine.Pin.IN)
pin19 = machine.Pin(19, machine.Pin.IN)
pin20 = machine.Pin(20, machine.Pin.IN)
pin21 = machine.Pin(21, machine.Pin.IN)
pin22 = machine.Pin(22, machine.Pin.IN)

pin23 = machine.Pin(23)  # Regulator PWM(Hi)-PFM(Lo) switch
pin24 = machine.Pin(24)  # VBUS sense

pin25 = machine.Pin(25, machine.Pin.OUT, value=IO_OFF)  # Onboard LED

adc0 = machine.ADC(machine.Pin(26))
adc1 = machine.ADC(machine.Pin(27))
adc2 = machine.ADC(machine.Pin(28))
adc3 = machine.ADC(machine.Pin(29))  # VSYS/3
adc4 = machine.ADC(machine.ADC.CORE_TEMP)  # temperature sensor


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
    :int bit: address bit
    :Pin scl: scl pin
    :Pin sda: sda pin
    """


class SpiConfig(namedtuple("SpiConfig", ["freq", "mode", "cspol", "sck", "mosi", "miso", "csel"])):
    """
    :int freq: frequency
    :int mode: clock/phase mode
    :Pin cspol: csel pin polarity
    :Pin sck: sck pin
    :Pin mosi: mosi pin
    :Pin miso: miso pin
    :Pin csel: csel pin
    """


class RaspberryScpiPico(MicroScpiDevice):
    kw_machine = ScpiKeyword("MACHINE", "MACHINE", None)
    kw_pin = ScpiKeyword("PIN", "PIN", ["14", "15", "16", "17", "18", "19", "20", "21", "22", "25", "?"])
    kw_in = ScpiKeyword("INput", "IN", None)
    kw_out = ScpiKeyword("OUTput", "OUT", None)
    kw_od = ScpiKeyword("ODrain", "OD", None)
    kw_led = ScpiKeyword("LED", "LED", ["?"])
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
    kw_i2c = ScpiKeyword("I2C", "I2C", ["0", "1", "?"])
    kw_scan = ScpiKeyword("SCAN", "SCAN", ["?"])
    kw_addr = ScpiKeyword("ADDRess", "ADDR", None)
    kw_bit = ScpiKeyword("BIT", "BIT", ["?"])
    kw_memory = ScpiKeyword("MEMory", "MEM", None)
    kw_freq = ScpiKeyword("FREQuency", "FREQ", ["?"])
    kw_spi = ScpiKeyword("SPI", "SPI", ["0", "1", "?"])
    kw_csel = ScpiKeyword("CSEL", "CS", None)
    kw_mode = ScpiKeyword("MODE", "MODE", ["?"])
    kw_pol = ScpiKeyword("POLarity", "POL", ["?"])
    kw_xfer = ScpiKeyword("TRANSfer", "TRANS", None)
    kw_adc = ScpiKeyword("ADC", "ADC", ["0", "1", "2", "3", "4"])
    kw_high = ScpiKeyword("HIGH", "HIGH", None)
    kw_low = ScpiKeyword("LOW", "LOW", None)
    kw_write = ScpiKeyword("WRITE", "WRITE", None)
    kw_read = ScpiKeyword("READ", "READ", ["?"])
    kw_value = ScpiKeyword("VALue", "VAL", ["?"])
    kw_def = ScpiKeyword("DEFault", "DEF", None)
    kw_transfer = ScpiKeyword("TRANSfer", "TRANS", None)
    kw_system = ScpiKeyword("SYSTem", "SYST", None)
    kw_error = ScpiKeyword("ERRor", "ERR", ["?"])

    "PIN[14|15|16|17|18|19|20|21|22|25]"
    pins = {
        14: pin14,
        15: pin15,
        16: pin16,
        17: pin17,
        18: pin18,
        19: pin19,
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
        3: adc3,
        4: adc4
    }
    spi = {
        0: spi0,
        1: spi1
    }
    pin_conf = {
        14: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        15: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        16: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        17: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        18: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        19: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        20: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        21: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        22: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN),
        25: PinConfig(machine.Pin.IN, IO_OFF, machine.Pin.PULL_DOWN)
    }
    pwm_conf = {
        14: PwmConfig(1000, 32768),
        15: PwmConfig(1000, 32768),
        16: PwmConfig(1000, 32768),
        17: PwmConfig(1000, 32768),
        18: PwmConfig(1000, 32768),
        19: PwmConfig(1000, 32768),
        20: PwmConfig(1000, 32768),
        21: PwmConfig(1000, 32768),
        22: PwmConfig(1000, 32768),
        25: PwmConfig(1000, 32768)
    }
    i2c_conf = {
        0: I2cConfig(100_000, 1, scl0, sda0),
        1: I2cConfig(100_000, 1, scl1, sda1)
    }
    spi_conf = {
        0: SpiConfig(1_000_000, SPI_MODE0, SPI_CSPOL_LO, sck0, mosi0, miso0, cs0),
        1: SpiConfig(1_000_000, SPI_MODE0, SPI_CSPOL_LO, sck1, mosi1, miso1, cs1)
    }

    def __init__(self):
        super().__init__()

        cls = ScpiCommand((self.kw_cls,), False, cb_do_nothing)
        ese = ScpiCommand((self.kw_ese,), False, cb_do_nothing)
        opc = ScpiCommand((self.kw_opc,), False, cb_do_nothing)
        rst = ScpiCommand((self.kw_rst,), False, self.cb_rst)
        sre = ScpiCommand((self.kw_sre,), False, cb_do_nothing)
        esr_q = ScpiCommand((self.kw_esr,), True, cb_do_nothing)
        idn_q = ScpiCommand((self.kw_idn,), True, self.cb_idn)
        stb_q = ScpiCommand((self.kw_stb,), True, cb_do_nothing)
        tst_q = ScpiCommand((self.kw_tst,), True, cb_do_nothing)

        machine_freq = ScpiCommand((self.kw_machine, self.kw_freq), False, self.cb_machine_freq)

        system_error = ScpiCommand((self.kw_system, self.kw_error), True, self.cb_system_error)

        pin_q = ScpiCommand((self.kw_pin,), True, self.cb_pin_status)
        pin_mode = ScpiCommand((self.kw_pin, self.kw_mode), False, self.cb_pin_mode)
        pin_val = ScpiCommand((self.kw_pin, self.kw_value), False, self.cb_pin_val)
        pin_on = ScpiCommand((self.kw_pin, self.kw_on), False, self.cb_pin_on)
        pin_off = ScpiCommand((self.kw_pin, self.kw_off), False, self.cb_pin_off)
        pin_pwm_freq = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_freq), False, self.cb_pin_pwm_freq)
        pin_pwm_duty = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_duty), False, self.cb_pin_pwm_duty)

        led_q = ScpiCommand((self.kw_led,), True, self.cb_led_status)
        led_val = ScpiCommand((self.kw_led, self.kw_value), True, self.cb_led_val)
        led_on = ScpiCommand((self.kw_led, self.kw_on), False, self.cb_led_on)
        led_off = ScpiCommand((self.kw_led, self.kw_off), False, self.cb_led_off)
        led_pwm_freq = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_freq), False, self.cb_led_pwm_freq)
        led_pwm_duty = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_duty), False, self.cb_led_pwm_duty)

        i2c_q = ScpiCommand((self.kw_i2c,), True, self.cb_i2c_status)
        i2c_scan_q = ScpiCommand((self.kw_i2c, self.kw_scan), True, self.cb_i2c_scan)
        i2c_freq = ScpiCommand((self.kw_i2c, self.kw_freq), False, self.cb_i2c_freq)
        i2c_abit = ScpiCommand((self.kw_i2c, self.kw_addr, self.kw_bit), False, self.cb_i2c_address_bit)
        i2c_write = ScpiCommand((self.kw_i2c, self.kw_write), False, self.cb_i2c_write)
        i2c_read_q = ScpiCommand((self.kw_i2c, self.kw_read), True, self.cb_i2c_read)
        i2c_write_memory = ScpiCommand((self.kw_i2c, self.kw_memory, self.kw_write), False, self.cb_i2c_write_memory)
        i2c_read_memory = ScpiCommand((self.kw_i2c, self.kw_memory, self.kw_read), True, self.cb_i2c_read_memory)

        spi_q = ScpiCommand((self.kw_spi,), True, self.cb_spi_status)
        spi_cs_pol = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_pol), False, self.cb_spi_cs_pol)
        spi_cs_val = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_value), False, self.cb_spi_cs_val)
        spi_mode = ScpiCommand((self.kw_spi, self.kw_mode), False, self.cb_spi_clock_phase)
        spi_freq = ScpiCommand((self.kw_spi, self.kw_freq), False, self.cb_spi_freq)
        spi_transfer = ScpiCommand((self.kw_spi, self.kw_transfer), False, self.cb_spi_tx)
        spi_write = ScpiCommand((self.kw_spi, self.kw_write), False, self.cb_spi_write)
        spi_read = ScpiCommand((self.kw_spi, self.kw_read), False, self.cb_spi_read)

        adc_read = ScpiCommand((self.kw_adc, self.kw_read), True, self.cb_adc_read)

        self.commands = [cls, ese, opc, rst, sre, esr_q, idn_q, stb_q, tst_q,
                         machine_freq,
                         system_error,
                         pin_q, pin_mode, pin_val, pin_on, pin_off, pin_pwm_freq, pin_pwm_duty,
                         led_q, led_val, led_on, led_off, led_pwm_freq, led_pwm_duty,
                         i2c_q, i2c_scan_q, i2c_freq, i2c_abit, i2c_write, i2c_read_q,
                         i2c_write_memory, i2c_read_memory,
                         spi_q, spi_cs_pol, spi_mode, spi_freq, spi_write, spi_read, spi_cs_val, spi_transfer,
                         adc_read,
                         ]

        self.error_indicate(False)

    @staticmethod
    def error_indicate(error=False):
        pin0.off()
        pin1.off()
        if error:
            pin1.on()
        else:
            pin0.on()

    def error_push(self, error_no):
        super().error_push(error_no)
        self.error_indicate(True)

    def cb_idn(self, param="", opt=None):
        """<Vendor name>,<Model number>,<Serial number>,<Firmware version>"""
        serial = "".join(f"{d:02x}" for d in machine.unique_id())

        query = (opt[-1] == "?")
        if query:
            print(f"RaspberryPiPico,RP001,{serial},0.0.1")
        else:
            self.error_push(E_SYNTAX)

    @staticmethod
    def cb_rst(param="", opt=None):
        """
        - *RST <No Param>
        """

        # print(f"Reset")
        machine.freq(DEFAULT_CPU_CLOCK)
        machine.soft_reset()

    @staticmethod
    def cb_version(param="", opt=None):
        """The command returns a string in the form of “YYYY.V”, where “YYYY” represents
        the year of the version and “V” represents a version for that year (e.g. 1997.0).
        """
        print("2023.04")

    def cb_machine_freq(self, param="", opt=None):
        """
        - MACHINE:FREQuency[?] num

        :return:
        """

        machine_freq = param
        query = (opt[-1] == "?")

        # print("cb_machine_freq", param, opt)
        if query:
            machine_freq = machine.freq()
            print(f"{machine_freq}")
        elif machine_freq is not None:
            # print("cb_machine_freq", param)

            try:
                machine_freq = int(float(machine_freq))
                if ABS_MIN_CLOCK < machine_freq < ABS_MAX_CLOCK:
                    machine.freq(machine_freq)
                else:
                    self.error_push(E_OUT_OF_RANGE)
            except TypeError:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_system_error(self, param="", opt=None):
        """
        - ``SYSTem:ERRor?``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        if query:
            if self.error_counter > 0:
                err = ERROR_LIST[self.error_rd_pointer]
                print(f"{err.id}, '{err.message}'")
                ERROR_LIST[self.error_rd_pointer] = E_NONE
                self.error_rd_pointer = (self.error_rd_pointer + 1) & 0xFF
                self.error_counter = max(self.error_counter - 1, 0)
            else:
                err = E_NONE
                print(f"{err.id}, '{err.message}'")

            self.error_indicate(True if self.error_counter > 0 else False)

        else:
            self.error_push(E_SYNTAX)

    def cb_pin_status(self, param="", opt=None):
        """
        - ``PIN?``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")

        if query:
            for pin in self.pin_conf.keys():
                conf = self.pin_conf[pin]
                pwm_conf = self.pwm_conf[pin]
                mode = conf.mode
                value = conf.value
                freq = pwm_conf.freq
                duty = pwm_conf.duty_u16
                message = ";".join([f"PIN{pin}:MODE {IO_MODE_STRINGS[mode]}",
                                    f"PIN{pin}:VALue {IO_VALUE_STRINGS[value]}",
                                    f"PIN{pin}:PWM:FREQuency {freq}",
                                    f"PIN{pin}:PWM:DUTY {duty}"
                                    ])
                print(message, end=";")
            print()
        else:
            self.error_push(E_SYNTAX)

    def cb_pin_val(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:VALue[?] 0|1|OFF|ON

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        query = (opt[-1] == "?")
        conf = self.pin_conf[pin_number]

        if query:
            # print("cb_pin_val", pin_number, "Query", param)
            val = pin.value()
            print(IO_VALUE_STRINGS[val])
        elif param is not None:
            # print("cb_pin_val", pin_number, param)
            if param == str(IO_ON) or self.kw_on.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_ON)
                vals = list(conf)
                vals[conf.index(conf.value)] = IO_ON
                self.pin_conf[pin_number] = PinConfig(*vals)
            elif param == str(IO_OFF) or self.kw_off.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_OFF)
                vals = list(conf)
                vals[conf.index(conf.value)] = IO_OFF
                self.pin_conf[pin_number] = PinConfig(*vals)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_mode(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:MODE INput|OUTput|ODrain|PWM

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
            # print("cb_pin_mode", pin_number, "Query", param)
            print(IO_MODE_STRINGS[conf.mode])
        elif param is not None:
            # print("cb_pin_mode", pin_number, param)
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
                self.error_push(E_INVALID_PARAMETER)

            pin.init(mode, alt=alt, pull=conf.pull)
            self.pins[pin_number] = pin
            vals = list(conf)
            vals[conf.index(conf.mode)] = mode
            self.pin_conf[pin_number] = PinConfig(*vals)
            # print(pin)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_on(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:ON
        - PIN[14|15|16|17|18|19|20|21|22|25]:OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        query = (opt[-1] == "?")

        if query:
            # print("cb_pin_on", pin_number, "Query", param)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_pin_on", pin_number, param)
            self.cb_pin_val(param="ON", opt=opt)

    def cb_pin_off(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:ON
        - PIN[14|15|16|17|18|19|20|21|22|25]:OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        query = (opt[-1] == "?")

        if query:
            # print("cb_pin_off", pin_number, "Query", param)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_pin_off", pin_number, param)
            self.cb_pin_val(param="OFF", opt=opt)

    def cb_pin_pwm_freq(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:PWM:FREQuency[?] num

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
            # print("cb_pin_pwm_freq", pin_number, "Query", param)
            pwm_freq = conf.freq
            print(f"{pwm_freq}")
        elif pwm_freq is not None:
            # print("cb_pin_pwm_freq", pin_number, param)

            pwm_freq = int(float(pwm_freq))

            if MIN_PWM_CLOCK <= pwm_freq <= MAX_PWM_CLOCK:
                pwm = machine.PWM(pin)
                pwm.freq(conf.freq)
                pwm.duty_u16(conf.duty_u16)
                # print(pwm)
                vals = list(conf)
                vals[conf.index(conf.freq)] = pwm_freq
                self.pwm_conf[pin_number] = PwmConfig(*vals)
            else:
                self.error_push(E_OUT_OF_RANGE)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_pwm_duty(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:PWM:DUTY[?] num

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
            # print("cb_pin_pwm_duty", pin_number, "Query", param)
            pwm_duty = conf.duty_u16
            print(f"{pwm_duty}")
        elif pwm_duty is not None:
            # print("cb_pin_pwm_duty", pin_number, param)

            pwm_duty = int(float(pwm_duty))

            if MIN_PWM_DUTY <= pwm_duty <= MAX_PWM_DUTY:
                pwm = machine.PWM(pin)
                pwm.freq(conf.freq)
                pwm.duty_u16(conf.duty_u16)
                # print(pwm)
                vals = list(conf)
                vals[conf.index(conf.duty_u16)] = pwm_duty
                self.pwm_conf[pin_number] = PwmConfig(*vals)
            else:
                self.error_push(E_OUT_OF_RANGE)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_led_status(self, param="", opt=None):
        """
        - ``LED?``

        :param param:
        :param opt:
        :return:
        """

        pin_number = 25
        query = (opt[-1] == "?")
        conf = self.pin_conf[pin_number]
        pwm_conf = self.pwm_conf[pin_number]
        value = conf.value
        freq = pwm_conf.freq
        duty = pwm_conf.duty_u16

        if query:
            print(f"LED:VALue {IO_VALUE_STRINGS[value]};LED:PWM:FREQuency {freq};LED:PWM:DUTY {duty}")
        else:
            self.error_push(E_SYNTAX)

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
            # print("cb_led_on", "Query", param)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_led_on", param)
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
            # print("cb_led_off", "Query", param)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_led_off", param)
            self.cb_pin_val(param="OFF", opt=opt)

    def cb_led_val(self, param, opt):
        """
        - LED:VALue[?] 0|1|OFF|ON

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")

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

        self.cb_pin_pwm_duty(param, opt)

    def cb_i2c_status(self, param="", opt=None):
        """
        - ``I2C?``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")

        if query:
            for bus in self.i2c_conf.keys():
                conf = self.i2c_conf[bus]
                shift = conf.bit
                freq = conf.freq
                print(f"I2C{bus}:ADDRess:BIT {shift};I2C{bus}:FREQuency {freq};", end="")
            else:
                print()
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_i2c_scan(self, param, opt):
        """
        - I2C[01]:SCAN?

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        if isinstance(opt[0], str):
            bus_number = int(opt[0])
            bus = self.i2c[bus_number]
            conf = self.i2c_conf[bus_number]
            shift = conf.bit
            if query:
                # print("cb_i2c_scan", "Query", param)
                scanned = bus.scan()
                if not scanned:
                    print(BUS_FAIL_CODE)
                else:
                    print(",".join([f"{(int(s) << shift):02x}" for s in scanned]))
            else:
                self.error_push(E_SYNTAX)
        else:
            self.error_push(E_SYNTAX)

    def cb_i2c_freq(self, param, opt):
        """
        - I2C[01]:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus_freq = param
        conf = self.i2c_conf[bus_number]

        if query:
            # print("cb_i2c_freq", bus_number, "Query", param)

            bus_freq = conf.freq
            print(f"{bus_freq}")
        elif bus_freq is not None:
            # print("cb_i2c_freq", bus_number, param)

            bus_freq = int(float(bus_freq))

            if MIN_I2C_CLOCK <= bus_freq <= MAX_I2C_CLOCK:
                bus = machine.I2C(bus_number, scl=conf.scl, sda=conf.sda, freq=bus_freq)
                self.i2c[bus_number] = bus
                vals = list(conf)
                vals[conf.index(conf.freq)] = bus_freq
                self.i2c_conf[bus_number] = I2cConfig(*vals)
            else:
                self.error_push(E_OUT_OF_RANGE)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_i2c_address_bit(self, param, opt):
        """
        - I2C[01]:ADDRess:BIT[?] 0|1|DEFault

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bit = param
        conf = self.i2c_conf[bus_number]

        if query:
            # print("cb_i2c_address_bit", "Query", param)

            bit = conf.bit
            print(f"{bit}")
        elif bit is not None:
            # print("cb_i2c_address_bit", param)
            if param in ["0", "1"]:
                vals = list(conf)
                vals[conf.index(conf.bit)] = int(param)
                self.i2c_conf[bus_number] = I2cConfig(*vals)
            elif self.kw_def.match(param).match:
                vals = list(conf)
                vals[conf.index(conf.bit)] = DEFAULT_I2C_BIT
                self.i2c_conf[bus_number] = I2cConfig(*vals)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]),(([0-9a-fA-F][0-9a-fA-F])+),([01])$")

        if query:
            # print("cb_i2c_write", "Query", param)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_i2c_write", param)
            searched = rstring.search(param)
            if searched is not None:
                address, data, _, stop = searched.groups()
                stop = bool(int(stop))
                address = int(f"0x{address}") >> shift
                data_array = int(f"0x{data}").to_bytes(ceil(len(data) / 2), "big")
                # print(f"0x{address:02x}", [f"0x{c:02x}" for c in data_array], stop)
                try:
                    bus.writeto(address, bytes(data_array), stop)
                except OSError:
                    self.error_push(E_I2C_FAIL)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_i2c_read(self, param, opt):
        """
        - I2C[01]:READ? address,length,stop

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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]),([1-9]|[1-9][0-9]+),([01])$")

        if query:
            # print("cb_i2c_read", "Query", param)
            if param is not None:
                # print("cb_i2c_read", param)

                searched = rstring.search(param)
                if searched is not None:
                    address, length, stop = searched.groups()
                    stop = bool(int(stop))
                    address = int(f"0x{address}") >> shift
                    # print(f"0x{address:02x}", length, stop)
                    try:
                        read = bus.readfrom(int(address), int(length), stop)
                        data = ",".join(f"{d:02x}" for d in read)
                        print(data)
                        return
                    except OSError:
                        self.error_push(E_I2C_FAIL)
                        print(BUS_FAIL_CODE)
                else:
                    self.error_push(E_INVALID_PARAMETER)
            else:
                self.error_push(E_MISSING_PARAM)
        else:
            self.error_push(E_SYNTAX)
            print(BUS_FAIL_CODE)

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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]),(([0-9a-fA-F][0-9a-fA-F])+),([0-9a-fA-F]+),([12])$")

        if query:
            # print("cb_i2c_write_memory", "Query", param)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_i2c_write_memory", param)

            searched = rstring.search(param)

            if searched is not None:
                address, memaddress, _, data, addrsize = searched.groups()
                # print(address, memaddress, data, addrsize)

                address = int(f"0x{address}") >> shift
                memaddress = int(f"0x{memaddress}")
                data_array = int(f"0x{data}").to_bytes(ceil(len(data) / 2), "big")
                addrsize = 8 * int(addrsize)
                # print(f"0x{address:02x}", f"0x{memaddress:02x}", [f"0x{c:02x}" for c in data_array], addrsize)
                try:
                    bus.writeto_mem(address, memaddress, data_array)
                except OSError:
                    self.error_push(E_I2C_FAIL)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]),(([0-9a-fA-F][0-9a-fA-F])+),([1-9]|[1-9][0-9]+),([12])$")

        if query:
            # print("cb_i2c_read_memory", "Query", param)

            if param is not None:
                searched = rstring.search(param)
                if searched is not None:
                    address, memaddress, _, length, addrsize = searched.groups()
                    address = int(f"0x{address}") >> shift
                    memaddress = int(f"0x{memaddress}")
                    length = int(f"0x{length}")
                    addrsize = 8 * int(addrsize)

                    try:
                        read = bus.readfrom_mem(address, memaddress, length)
                        data = ",".join(f"{d:02x}" for d in read)
                        print(data)
                        return
                    except OSError:
                        self.error_push(E_I2C_FAIL)
                        print(BUS_FAIL_CODE)
                else:
                    self.error_push(E_INVALID_PARAMETER)
            else:
                self.error_push(E_MISSING_PARAM)
        else:
            self.error_push(E_SYNTAX)
        print(BUS_FAIL_CODE)

    def cb_adc_read(self, param, opt):
        """
        - ADC[01234]:READ?

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        adc_ch = int(opt[0])
        adc = self.adc[adc_ch]

        if query:
            # print("cb_adc_read", "Query", param)
            value = adc.read_u16()
            print(f"{value}")  # decimal
        else:
            self.error_push(E_SYNTAX)

    def cb_spi_status(self, param="", opt=None):
        """
        - ``SPI?``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")

        if query:
            for bus in self.spi_conf.keys():
                conf = self.spi_conf[bus]
                cspol = conf.cspol
                freq = conf.freq
                mode = conf.mode
                print(f"SPI{bus}:CSEL:POLarity {cspol};SPI{bus}:FREQuency {freq};SPI{bus}:MODE {mode};", end="")
            print()
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_cs_pol(self, param, opt):
        """
        - SPI[01]:CSEL:POLarity[?] 0|1|DEFault

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        conf = self.spi_conf[bus_number]
        cspol = param

        if query:
            # print("cb_spi_cs_pol", "Query", param)
            cspol = conf.cspol
            print(cspol)
        elif cspol is not None:
            # print("cb_spi_cs_pol", param)
            if cspol in ["0", "1"]:
                vals = list(conf)
                vals[conf.index(conf.cspol)] = int(cspol)
                self.spi_conf[bus_number] = SpiConfig(*vals)
                self.cb_spi_cs_val("OFF", [bus_number])
            elif self.kw_def.match(param).match:
                vals = list(conf)
                vals[conf.index(conf.cspol)] = DEFAULT_SPI_CSPOL
                self.spi_conf[bus_number] = SpiConfig(*vals)
                self.cb_spi_cs_val("OFF", [bus_number])
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_cs_val(self, param, opt):
        """
        - SPI[01]:CSEL:VALue[?] 0|1|OFF|ON

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        conf = self.spi_conf[bus_number]
        cs_pin = conf.csel
        cs_pol = conf.cspol

        if query:
            # print("cb_spi_cs_val", "Query", param)
            print(IO_VALUE_STRINGS[int(cs_pin.value() ^ (not cs_pol))])
        elif param is not None:
            # print("cb_spi_cs_val", param)
            if param == str(SPI_CSPOL_HI) or self.kw_on.match(param).match:
                cs_pin.value(int(not (cs_pol ^ SPI_CSPOL_HI)))
            elif param == str(SPI_CSPOL_LO) or self.kw_off.match(param).match:
                cs_pin.value(int(not (cs_pol ^ SPI_CSPOL_LO)))
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_clock_phase(self, param, opt):
        """
        - SPI[01]:MODE[?] 0|1|2|3|DEFault

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.spi[bus_number]
        conf = self.spi_conf[bus_number]
        mode = param
        vals = list(conf)

        if query:
            # print("cb_spi_clock_phase", "Query", param)
            print(conf.mode)
        elif mode is not None:
            # print("cb_spi_clock_phase", param)
            if self.kw_def.match(param).match:
                vals[conf.index(conf.mode)] = DEFAULT_SPI_MODE
                conf = SpiConfig(*vals)

                bus = machine.SPI(bus_number, baudrate=conf.freq, sck=conf.sck, mosi=conf.mosi, miso=conf.miso,
                                  polarity=DEFAULT_SPI_CKPOL, phase=DEFAULT_SPI_CKPH)
            elif mode in ["0", "1", "2", "3"]:
                mode = int(mode)
                ckpol = SPI_CKPOL_HI if mode & SPI_MASK_CKPOL else SPI_CKPOL_LO
                ckph = SPI_CKPH_HI if mode & SPI_MASK_CKPH else SPI_CKPH_LO

                vals[conf.index(conf.mode)] = int(mode)
                conf = SpiConfig(*vals)

                bus = machine.SPI(bus_number, baudrate=conf.freq, sck=conf.sck, mosi=conf.mosi, miso=conf.miso,
                                  polarity=ckpol, phase=ckph)
            else:
                self.error_push(E_INVALID_PARAMETER)

            self.spi_conf[bus_number] = conf
            self.spi[bus_number] = bus
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_freq(self, param, opt):
        """
        - SPI[01]:FREQuency[?] num

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus_freq = param
        conf = self.spi_conf[bus_number]
        vals = list(conf)

        if query:
            # print("cb_spi_freq", bus_number, "Query", param)

            bus_freq = conf.freq
            print(f"{bus_freq}")
        elif bus_freq is not None:
            # print("cb_spi_freq", bus_number, param)
            try:
                bus_freq = int(float(bus_freq))

                if MIN_SPI_CLOCK <= bus_freq <= MAX_SPI_CLOCK:
                    ckpol = SPI_CKPOL_HI if conf.mode & SPI_MASK_CKPOL else SPI_CKPOL_LO
                    ckph = SPI_CKPH_HI if conf.mode & SPI_MASK_CKPH else SPI_CKPH_LO

                    bus = machine.SPI(bus_number, baudrate=bus_freq, sck=conf.sck, mosi=conf.mosi, miso=conf.miso,
                                      polarity=ckpol, phase=ckph)
                    self.spi[bus_number] = bus

                    vals[conf.index(conf.freq)] = bus_freq
                    self.spi_conf[bus_number] = SpiConfig(*vals)
                else:
                    self.error_push(E_OUT_OF_RANGE)
            except ValueError:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_tx(self, param, opt):
        """
        - ``SPI[01]:TRANSfer data,pre_cs,post_cs``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.spi[bus_number]

        rstring = re.compile(r"^(([0-9a-fA-F].)+),([oO][nN]|[oO][fF].|[01]),([oO][nN]|[oO][fF].|[01])$")

        if query:
            # print("cb_spi_tx", bus_number, "Query", param)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_spi_tx", bus_number, param)
            searched = rstring.search(param)
            if searched is not None:
                data, _, pre_cs, post_cs = searched.groups()
                # print(f"0x{data}")
                string_length = len(data)
                data_array = tuple(int(data[i:i + 2], 16) for i in range(0, string_length, 2))
                length = len(data_array)
                read_data_array = bytearray([0] * length)
                # print([hex(c) for c in data_array])
                try:
                    self.cb_spi_cs_val(pre_cs, [bus_number, ""])
                    bus.write_readinto(bytes(data_array), read_data_array)
                    self.cb_spi_cs_val(post_cs, [bus_number, ""])
                    data = ",".join(f"{d:02x}" for d in read_data_array)
                    print(data)
                except OSError:
                    self.error_push(E_SPI_FAIL)
                    print(BUS_FAIL_CODE)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_write(self, param, opt):
        """
        - ``SPI[01]:WRITE data,pre_cs,post_cs``

        :param param:
        :param opt:
        :return:
        """
        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.spi[bus_number]
        rstring = re.compile(r"^(([0-9a-fA-F].)+),([oO][nN]|[oO][fF].|[01]),([oO][nN]|[oO][fF].|[01])$")

        if query:
            # print("cb_spi_write", bus_number, "Query", param)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_spi_write", bus_number, param)
            searched = rstring.search(param)
            if searched is not None:
                data, _, pre_cs, post_cs = searched.groups()
                # print(f"0x{data}")
                string_length = len(data)
                data_array = (int(data[i:i + 2], 16) for i in range(0, string_length, 2))
                # print([hex(c) for c in data_array])
                try:
                    self.cb_spi_cs_val(pre_cs, [bus_number, ""])
                    bus.write(bytes(data_array))
                    self.cb_spi_cs_val(post_cs, [bus_number, ""])
                except OSError:
                    self.error_push(E_SPI_FAIL)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_spi_read(self, param, opt):
        """
        - ``SPI[01]:READ? length,mask,pre_cs,post_cs``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus = self.spi[bus_number]
        rstring = re.compile(
            r"^([1-9]|[1-9][0-9]+),([0-9a-fA-F].),([oO][nN]|[oO][fF].|[01]),([oO][nN]|[oO][fF].|[01])$")

        if query:
            # print("cb_spi_read", bus_number, "Query", param)
            searched = rstring.search(param)

            if searched is not None:
                length, mask, pre_cs, post_cs = searched.groups()
                # print(length, mask)
                try:
                    data_array = bytearray([0] * int(length))
                    mask = int("0x" + mask)
                    self.cb_spi_cs_val(pre_cs, [bus_number, ""])
                    bus.readinto(data_array, mask)
                    self.cb_spi_cs_val(post_cs, [bus_number, ""])
                    data = ",".join(f"{d:02x}" for d in data_array)
                    print(data)
                    return
                except OSError:
                    self.error_push(E_SPI_FAIL)
                except ValueError:
                    self.error_push(E_INVALID_PARAMETER)
            else:
                self.error_push(E_INVALID_PARAMETER)
        elif param is not None:
            self.error_push(E_SYNTAX)
        else:
            self.error_push(E_MISSING_PARAM)
