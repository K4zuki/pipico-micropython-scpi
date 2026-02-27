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
from micropython import const
from collections import OrderedDict

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

- MACHINE:FREQuency[?] num|DEFault|MINimum|MAXimum

- SYSTem:ERRor?

- PIN?
- PIN[14|15|16|17|18|19|20|21|22|25]:MODE[?] INput|OUTput|ODrain|PWM|DEFault
- PIN[14|15|16|17|18|19|20|21|22|25]:VALue[?] 0|1|OFF|ON|DEFault
- PIN[14|15|16|17|18|19|20|21|22|25]:ON
- PIN[14|15|16|17|18|19|20|21|22|25]:OFF

- PWM?
- PWM[14|15|16|17|18|19|20|21|22|25]:ON
- PWM[14|15|16|17|18|19|20|21|22|25]:OFF
- PWM[14|15|16|17|18|19|20|21|22|25]:FREQuency[?] num|DEFault|MINimum|MAXimum
- PWM[14|15|16|17|18|19|20|21|22|25]:DUTY[?] num|DEFault|MINimum|MAXimum

- LED?
- LED:ON
- LED:OFF
- LED:VALue[?] 0|1|OFF|ON|DEFault
- LED:PWM:ON
- LED:PWM:OFF
- LED:PWM:FREQuency[?] num|DEFault|MINimum|MAXimum
- LED:PWM:DUTY[?] num|DEFault|MINimum|MAXimum

- I2C?
- I2C[01]:SCAN?
- I2C[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
- I2C[01]:ADDRess:BIT[?] 0|1|DEFault
- I2C[01]:WRITE address,buffer,stop
- I2C[01]:READ? address,length,stop
- I2C[01]:MEMory:WRITE address,memaddress,buffer,addrsize
- I2C[01]:MEMory:READ address,memaddress,nbytes,addrsize

- SPI?
- SPI[01]:CSEL:POLarity[?] 0|1|DEFault
- SPI[01]:CSEL:VALue[?] 0|1|OFF|ON
- SPI[01]:MODE[?] 0|1|2|3|DEFault
- SPI[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
- SPI[01]:TRANSfer data,pre_cs,post_cs
- SPI[01]:WRITE data,pre_cs,post_cs
- SPI[01]:READ? length,mask,pre_cs,post_cs

- ADC[01234]:READ?

"""
from micropython import const
import sys
import machine

import re
from math import ceil
from collections import namedtuple
from MicroScpiDevice import ScpiKeyword, ScpiCommand, ScpiErrorNumber, MicroScpiDevice, cb_do_nothing, ERROR_LIST

ABS_MAX_CLOCK = const(264_000_000)
DEFAULT_CPU_CLOCK = const(125_000_000)
ABS_MIN_CLOCK = const(100_000_000)
MAX_PWM_CLOCK = const(100_000)
MIN_PWM_CLOCK = const(1_000)
DEFAULT_PWM_CLOCK = const(1000)
MAX_PWM_DUTY = const(65535)
MIN_PWM_DUTY = const(0)
DEFAULT_PWM_DUTY = const(32768)
MAX_I2C_CLOCK = const(400_000)
MIN_I2C_CLOCK = const(10_000)
DEFAULT_I2C_CLOCK = const(100_000)
MAX_SPI_CLOCK = const(10_000_000)
MIN_SPI_CLOCK = const(10_000)
DEFAULT_SPI_CLOCK = const(1_000_000)
MAX_UART_BAUD = const(500_000)
MIN_UART_BAUD = const(300)
IO_ON = 1
IO_OFF = 0
IO_VALUE_STRINGS = {IO_ON: "ON", IO_OFF: "OFF"}
IO_MODE_STRINGS = {machine.Pin.IN: "IN", machine.Pin.OUT: "OUT",
                   machine.Pin.OPEN_DRAIN: "ODrain", machine.Pin.ALT: "PWM"}
DEFAULT_IO_VALUE = IO_OFF
DEFAULT_IO_MODE = machine.Pin.IN
DEFAULT_IO_PULL = machine.Pin.PULL_DOWN
DEFAULT_I2C_BIT = const(1)
SPI_MODE0 = const(0)
SPI_MODE1 = const(1)
SPI_MODE2 = const(2)
SPI_MODE3 = const(3)
DEFAULT_SPI_MODE = SPI_MODE0
SPI_CSPOL_HI = const(1)
SPI_CSPOL_LO = const(0)
DEFAULT_SPI_CSPOL = SPI_CSPOL_LO
SPI_MASK_CKPOL = const(0x02)
SPI_CKPOL_HI = const(1)
SPI_CKPOL_LO = const(0)
DEFAULT_SPI_CKPOL = SPI_CKPOL_LO
SPI_MASK_CKPH = const(0x01)
SPI_CKPH_HI = const(1)
SPI_CKPH_LO = const(0)
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
E_INVALID_PARAMETER = ScpiErrorNumber(-224, "Invalid parameter value")
E_I2C_FAIL = ScpiErrorNumber(-333, "I2C bus error")
E_SPI_FAIL = ScpiErrorNumber(-334, "SPI bus error")

pin0 = machine.Pin(0, mode=machine.Pin.OUT, value=IO_ON)  # no-error indicator
pin1 = machine.Pin(1, mode=machine.Pin.OUT, value=IO_OFF)  # error indicator

sck0 = machine.Pin(2)
mosi0 = machine.Pin(3)
miso0 = machine.Pin(4)
spi0 = machine.SPI(0, sck=sck0, mosi=mosi0, miso=miso0)
cs0 = machine.Pin(5, mode=machine.Pin.OUT, value=IO_ON)

sda1 = machine.Pin(6)
scl1 = machine.Pin(7)
i2c1 = machine.I2C(1, scl=scl1, sda=sda1, freq=DEFAULT_I2C_CLOCK)

sda0 = machine.Pin(8)
scl0 = machine.Pin(9)
i2c0 = machine.I2C(0, scl=scl0, sda=sda0, freq=DEFAULT_I2C_CLOCK)

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


class PinConfig(namedtuple("PinConfig", [
    "mode",  # Pin.IN|OUT|OPEN_DRAIN|ALT
    "value",  # 1/0
    "pull"  # Pin.PULL_UP|PULL_DOWN
])):
    """
    * ``mode``: ``Pin.IN|OUT|OPEN_DRAIN|ALT``
    * ``value``: ``1/0``
    * ``pull``: ``Pin.PULL_UP|PULL_DOWN``
    """


DEFAULT_PIN_CONFIG = PinConfig(DEFAULT_IO_MODE, DEFAULT_IO_VALUE, DEFAULT_IO_PULL)


class PwmConfig(namedtuple("PwmConfig", [
    "freq",  # frequency
    "duty_u16"  # duty
])):
    """
    :int freq: frequency
    :int duty_u16: duty
    """


DEFAULT_PWM_CONFIG = PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY)


class I2cConfig(namedtuple("I2cConfig", [
    "freq",  # frequency
    "bit",  # address bit
    "scl",  # scl pin
    "sda"  # sda pin
])):
    """
    :int freq: frequency
    :int bit: address bit
    :Pin scl: scl pin
    :Pin sda: sda pin
    """


class SpiConfig(namedtuple("SpiConfig", [
    "freq",  # frequency
    "mode",  # clock/phase mode
    "cspol",  # csel pin polarity
    "sck",  # sck pin
    "mosi",  # mosi pin
    "miso",  # miso pin
    "csel"  # csel pin
])):
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
    kw_pwm = ScpiKeyword("PWM", "PWM", ["14", "15", "16", "17", "18", "19", "20", "21", "22", "25", "?"])
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
    kw_min = ScpiKeyword("MINimum", "MIN", None)
    kw_max = ScpiKeyword("MAXimum", "MAX", None)

    "PIN[14|15|16|17|18|19|20|21|22|25]"
    pins = OrderedDict({
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
    })
    pwmv = OrderedDict({
        14: 0,
        15: 0,
        16: 0,
        17: 0,
        18: 0,
        19: 0,
        20: 0,
        21: 0,
        22: 0,
        25: 0
    })
    i2c = OrderedDict({
        0: i2c0,
        1: i2c1
    })
    adc = OrderedDict({
        0: adc0,
        1: adc1,
        2: adc2,
        3: adc3,
        4: adc4
    })
    spi = OrderedDict({
        0: spi0,
        1: spi1
    })
    pin_conf = OrderedDict({
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
    })
    pwm_conf = OrderedDict({
        14: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        15: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        16: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        17: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        18: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        19: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        20: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        21: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        22: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY),
        25: PwmConfig(DEFAULT_PWM_CLOCK, DEFAULT_PWM_DUTY)
    })
    i2c_conf = OrderedDict({
        0: I2cConfig(DEFAULT_I2C_CLOCK, DEFAULT_I2C_BIT, scl0, sda0),
        1: I2cConfig(DEFAULT_I2C_CLOCK, DEFAULT_I2C_BIT, scl1, sda1)
    })
    spi_conf = OrderedDict({
        0: SpiConfig(DEFAULT_SPI_CLOCK, SPI_MODE0, SPI_CSPOL_LO, sck0, mosi0, miso0, cs0),
        1: SpiConfig(DEFAULT_SPI_CLOCK, SPI_MODE0, SPI_CSPOL_LO, sck1, mosi1, miso1, cs1)
    })

    def __init__(self):
        super().__init__()
        self.stdout = sys.stdout

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

        pwm_q = ScpiCommand((self.kw_pwm,), True, self.cb_pwm_status)
        pwm_freq = ScpiCommand((self.kw_pwm, self.kw_freq), False, self.cb_pin_pwm_freq)
        pwm_duty = ScpiCommand((self.kw_pwm, self.kw_duty), False, self.cb_pin_pwm_duty)
        pwm_on = ScpiCommand((self.kw_pwm, self.kw_on), False, self.cb_pin_pwm_on)
        pwm_off = ScpiCommand((self.kw_pwm, self.kw_off), False, self.cb_pin_pwm_off)

        led_q = ScpiCommand((self.kw_led,), True, self.cb_led_status)
        led_val = ScpiCommand((self.kw_led, self.kw_value), True, self.cb_led_val)
        led_on = ScpiCommand((self.kw_led, self.kw_on), False, self.cb_led_on)
        led_off = ScpiCommand((self.kw_led, self.kw_off), False, self.cb_led_off)
        led_pwm_freq = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_freq), False, self.cb_led_pwm_freq)
        led_pwm_duty = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_duty), False, self.cb_led_pwm_duty)
        led_pwm_on = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_on), False, self.cb_led_pwm_on)
        led_pwm_off = ScpiCommand((self.kw_led, self.kw_pwm, self.kw_off), False, self.cb_led_pwm_off)

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
                         pin_q, pin_mode, pin_val, pin_on, pin_off,
                         pwm_q, pwm_freq, pwm_duty, pwm_on, pwm_off,
                         led_q, led_val, led_on, led_off, led_pwm_freq, led_pwm_duty, led_pwm_on, led_pwm_off,
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
            print(f"RaspberryPiPico,RP001,{serial},0.0.1", file=self.stdout)
        else:
            self.error_push(E_SYNTAX)

    def cb_rst(self, param="", opt=None):
        """
        - *RST <No Param>
        """

        # print(f"Reset", file=sys.stderr)
        machine.freq(DEFAULT_CPU_CLOCK)
        # machine.soft_reset()

        for pin in self.pins.values():
            pin.init(DEFAULT_IO_MODE)
        for pin_cfg in self.pin_conf.keys():
            self.pin_conf[pin_cfg] = DEFAULT_PIN_CONFIG
        for pwm_cfg in self.pwm_conf.keys():
            self.pwm_conf[pwm_cfg] = DEFAULT_PWM_CONFIG
        for pwmv in self.pwmv.keys():
            self.pwmv[pwmv] = 0
        for spi in self.spi.values():
            spi.deinit()
            spi.init()
        for spi_k in self.spi_conf.keys():
            self.spi_conf[spi_k] = SpiConfig(DEFAULT_SPI_CLOCK, SPI_MODE0, SPI_CSPOL_LO,
                                             self.spi_conf[spi_k].sck, self.spi_conf[spi_k].mosi,
                                             self.spi_conf[spi_k].miso, self.spi_conf[spi_k].csel)
            self.spi_conf[spi_k].csel.init()

        # There is no I2C.deinit(); I2C.init() is denied for some reason
        self.i2c[0] = machine.I2C(0, scl=scl0, sda=sda0, freq=DEFAULT_I2C_CLOCK)
        self.i2c[1] = machine.I2C(1, scl=scl1, sda=sda1, freq=DEFAULT_I2C_CLOCK)
        for i2c_k in self.i2c_conf.keys():
            self.i2c_conf[i2c_k] = I2cConfig(DEFAULT_I2C_CLOCK, DEFAULT_I2C_BIT,
                                             self.i2c_conf[i2c_k].scl, self.i2c_conf[i2c_k].sda)

    @staticmethod
    def cb_version(param="", opt=None):
        """The command returns a string in the form of “YYYY.V”, where “YYYY” represents
        the year of the version and “V” represents a version for that year (e.g. 1997.0).
        """
        print("2023.04", file=sys.stderr)

    def cb_machine_freq(self, param="", opt=None):
        """
        - MACHINE:FREQuency[?] num|DEFault|MINimum|MAXimum

        :return:
        """

        machine_freq = param
        query = (opt[-1] == "?")

        # print("cb_machine_freq", param, opt, file=sys.stderr)
        if query:
            if self.kw_def.match(param).match:
                machine_freq = DEFAULT_CPU_CLOCK
            elif self.kw_max.match(param).match:
                machine_freq = ABS_MAX_CLOCK
            elif self.kw_min.match(param).match:
                machine_freq = ABS_MIN_CLOCK
            else:
                machine_freq = machine.freq()

            print(f"{machine_freq:_d}", file=self.stdout)
        elif machine_freq is not None:
            # print("cb_machine_freq", param, file=sys.stderr)

            try:
                if self.kw_def.match(machine_freq).match:
                    machine_freq = DEFAULT_CPU_CLOCK
                elif self.kw_max.match(param).match:
                    machine_freq = ABS_MAX_CLOCK - 1
                elif self.kw_min.match(param).match:
                    machine_freq = ABS_MIN_CLOCK + 1
                else:
                    machine_freq = int(float(machine_freq))

                if ABS_MIN_CLOCK <= machine_freq <= ABS_MAX_CLOCK:
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
                print(f"{err.id}, '{err.message}'", file=self.stdout)
                ERROR_LIST[self.error_rd_pointer] = E_NONE
                self.error_rd_pointer = (self.error_rd_pointer + 1) & 0xFF
                self.error_counter = max(self.error_counter - 1, 0)
            else:
                err = E_NONE
                print(f"{err.id}, '{err.message}'", file=self.stdout)

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
                mode = conf.mode
                value = conf.value
                message = ";".join([f"PIN{pin}:MODE {IO_MODE_STRINGS[mode]}",
                                    f"PIN{pin}:VALue {IO_VALUE_STRINGS[value]}",
                                    ])
                print(message, end=";", file=self.stdout)
            print("", file=self.stdout)
        else:
            self.error_push(E_SYNTAX)

    def cb_pin_val(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:VALue[?] 0|1|OFF|ON|DEFault
        - DEFault is OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        query = (opt[-1] == "?")
        conf = self.pin_conf[pin_number]

        if query:
            # print("cb_pin_val", pin_number, "Query", param, file=sys.stderr)
            if param is not None:
                if self.kw_def.match(param).match:
                    val = DEFAULT_IO_VALUE
                else:
                    self.error_push(E_INVALID_PARAMETER)
                    return
            else:
                val = pin.value()
            print(IO_VALUE_STRINGS[val], file=self.stdout)
        elif param is not None:
            # print("cb_pin_val", pin_number, param, file=sys.stderr)
            if param == str(IO_ON) or self.kw_on.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_ON)
                self.pin_conf[pin_number] = PinConfig(machine.Pin.OUT, IO_ON, conf.pull)
            elif param == str(IO_OFF) or self.kw_off.match(param).match or self.kw_def.match(param).match:
                pin.init(machine.Pin.OUT, value=IO_OFF)
                self.pin_conf[pin_number] = PinConfig(machine.Pin.OUT, IO_OFF, conf.pull)
            else:
                self.error_push(E_INVALID_PARAMETER)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_mode(self, param="", opt=None):
        """
        - PIN[14|15|16|17|18|19|20|21|22|25]:MODE[?] INput|OUTput|ODrain|PWM|DEFault
        - DEFault is INput

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
            # print("cb_pin_mode", pin_number, "Query", param, file=sys.stderr)
            if param is not None:
                if self.kw_def.match(param).match:
                    mode = DEFAULT_IO_MODE
                else:
                    self.error_push(E_INVALID_PARAMETER)
                    return
            print(IO_MODE_STRINGS[mode], file=self.stdout)
        elif param is not None:
            # print("cb_pin_mode", pin_number, param, file=sys.stderr)
            if self.kw_in.match(param).match or self.kw_def.match(param).match:
                mode = machine.Pin.IN
            elif self.kw_out.match(param).match:
                mode = machine.Pin.OUT
            elif self.kw_od.match(param).match:
                mode = machine.Pin.OPEN_DRAIN
            elif self.kw_pwm.match(param).match:
                self.cb_pin_pwm_on("cb_pin_mode", opt)
                mode = machine.Pin.ALT
                alt = machine.Pin.ALT_PWM
            else:
                self.error_push(E_INVALID_PARAMETER)
                return

            pin.init(mode, alt=alt, pull=conf.pull)
            self.pins[pin_number] = pin
            self.pin_conf[pin_number] = PinConfig(mode, conf.value, conf.pull)
            # print(pin, file=sys.stderr)
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
            # print("cb_pin_on", pin_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_pin_on", pin_number, param, file=sys.stderr)
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
            # print("cb_pin_off", pin_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_pin_off", pin_number, param, file=sys.stderr)
            self.cb_pin_val(param="OFF", opt=opt)

    def cb_pwm_status(self, param="", opt=None):
        """
        - ``PWM?``

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")

        if query:
            for pin in self.pin_conf.keys():
                pwm_conf = self.pwm_conf[pin]
                freq = pwm_conf.freq
                duty = pwm_conf.duty_u16
                message = ";".join([f"PWM{pin}:FREQuency {freq:_d}",
                                    f"PWM{pin}:DUTY {duty:_d}"
                                    ])
                print(message, end=";", file=self.stdout)
            print("", file=self.stdout)
        else:
            self.error_push(E_SYNTAX)

    def cb_pin_pwm_freq(self, param="", opt=None):
        """
        - PWM[14|15|16|17|18|19|20|21|22|25]:FREQuency[?] num|DEFault|MINimum|MAXimum
        - DEFault is 1000 [Hz]

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
            # print("cb_pin_pwm_freq", pin_number, "Query", param, file=sys.stderr)
            if param is not None:
                if self.kw_def.match(param).match:
                    pwm_freq = DEFAULT_PWM_CLOCK
                elif self.kw_max.match(param).match:
                    pwm_freq = MAX_PWM_CLOCK
                elif self.kw_min.match(param).match:
                    pwm_freq = MIN_PWM_CLOCK
                else:
                    self.error_push(E_INVALID_PARAMETER)
                    return
            else:
                pwm_freq = conf.freq
            print(f"{pwm_freq:_d}", file=self.stdout)
        elif pwm_freq is not None:
            # print("cb_pin_pwm_freq", pin_number, param, file=sys.stderr)
            if self.kw_def.match(pwm_freq).match:
                pwm_freq = DEFAULT_PWM_CLOCK
            elif self.kw_max.match(param).match:
                pwm_freq = MAX_PWM_CLOCK
            elif self.kw_min.match(param).match:
                pwm_freq = MIN_PWM_CLOCK
            else:
                try:
                    pwm_freq = int(float(pwm_freq))
                except:
                    self.error_push(E_INVALID_PARAMETER)
                    return

            if MIN_PWM_CLOCK <= pwm_freq <= MAX_PWM_CLOCK:
                if self.pwmv[pin_number] == 1:
                    pwm = machine.PWM(pin, freq=pwm_freq, duty_u16=conf.duty_u16)
                    pwm.freq(pwm_freq)
                    pwm.duty_u16(conf.duty_u16)
                # print(pwm, file=sys.stderr)
                vals = list(conf)
                vals[conf.index(conf.freq)] = pwm_freq
                self.pwm_conf[pin_number] = PwmConfig(*vals)
            else:
                self.error_push(E_OUT_OF_RANGE)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_pwm_duty(self, param="", opt=None):
        """
        - PWM[14|15|16|17|18|19|20|21|22|25]:DUTY[?] num|DEFault|MINimum|MAXimum
        - DEFault is 32768

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
            # print("cb_pin_pwm_duty", pin_number, "Query", param, file=sys.stderr)
            if pwm_duty is not None:
                if self.kw_def.match(param).match:
                    pwm_duty = DEFAULT_PWM_DUTY
                elif self.kw_max.match(param).match:
                    pwm_duty = MAX_PWM_DUTY
                elif self.kw_min.match(param).match:
                    pwm_duty = MIN_PWM_DUTY
                else:
                    self.error_push(E_INVALID_PARAMETER)
                    return
            else:
                pwm_duty = conf.duty_u16
            print(f"{pwm_duty:_d}", file=self.stdout)
        elif pwm_duty is not None:
            # print("cb_pin_pwm_duty", pin_number, param, file=sys.stderr)

            if self.kw_def.match(pwm_duty).match:
                pwm_duty = DEFAULT_PWM_DUTY
            elif self.kw_max.match(param).match:
                pwm_duty = MAX_PWM_DUTY
            elif self.kw_min.match(param).match:
                pwm_duty = MIN_PWM_DUTY
            else:
                try:
                    pwm_duty = int(float(pwm_duty))
                except:
                    self.error_push(E_INVALID_PARAMETER)
                    return

            if MIN_PWM_DUTY <= pwm_duty <= MAX_PWM_DUTY:
                if self.pwmv[pin_number] == 1:
                    pwm = machine.PWM(pin, freq=conf.freq, duty_u16=pwm_duty)
                    pwm.freq(conf.freq)
                    pwm.duty_u16(pwm_duty)
                    # print(pin, pwm)
                # print(pwm, file=sys.stderr)
                vals = list(conf)
                vals[conf.index(conf.duty_u16)] = pwm_duty
                self.pwm_conf[pin_number] = PwmConfig(*vals)
            else:
                self.error_push(E_OUT_OF_RANGE)
        else:
            self.error_push(E_MISSING_PARAM)

    def cb_pin_pwm_on(self, param="", opt=None):
        """
        - PWM[14|15|16|17|18|19|20|21|22|25]:ON

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        conf = self.pwm_conf[pin_number]
        query = (opt[-1] == "?")

        if query:
            # print("cb_pin_pwm_on", pin_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is None:
            # print("cb_pin_pwm_on", pin_number, file=sys.stderr)
            pwm = machine.PWM(pin)
            pwm.init(freq=conf.freq, duty_u16=conf.duty_u16)
            self.pwmv[pin_number] = 1
            self.cb_pin_mode("PWM", opt)
        elif param != "cb_pin_mode":
            self.error_push(E_SYNTAX)

    def cb_pin_pwm_off(self, param="", opt=None):
        """
        - PWM[14|15|16|17|18|19|20|21|22|25]:OFF

        :param param:
        :param opt:
        :return:
        """

        pin_number = int(opt[0])
        pin = self.pins[pin_number]
        conf = self.pwm_conf[pin_number]
        query = (opt[-1] == "?")

        if query:
            # print("cb_pin_pwm_off", pin_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is None:
            # print("cb_pin_pwm_off", pin_number, file=sys.stderr)
            self.pwmv[pin_number] = 0
            pin.init(DEFAULT_IO_MODE)
            self.cb_pin_mode("IN", opt)
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
            print(f"LED:VALue {IO_VALUE_STRINGS[value]};LED:PWM:FREQuency {freq:_d};LED:PWM:DUTY {duty:_d}",
                  file=self.stdout)
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
            # print("cb_led_on", "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_led_on", param, file=sys.stderr)
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
            # print("cb_led_off", "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        else:
            # print("cb_led_off", param, file=sys.stderr)
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
        - LED:PWM:FREQuency[?] num|DEFault|MINimum|MAXimum
        - DEFault is 2000 [Hz]

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
        - LED:PWM:DUTY[?] num|DEFault|MINimum|MAXimum
        - DEFault is 32768

        :param param:
        :param List[str] opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")
        pwm_duty = param

        self.cb_pin_pwm_duty(param, opt)

    def cb_led_pwm_on(self, param="", opt=None):
        """
        - LED:PWM:ON

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")
        pwm_duty = param

        self.cb_pin_pwm_on(param, opt)

    def cb_led_pwm_off(self, param="", opt=None):
        """
        - LED:PWM:OFF

        :param param:
        :param opt:
        :return:
        """

        opt[0] = "25"
        query = (opt[-1] == "?")
        pwm_duty = param

        self.cb_pin_pwm_off(param, opt)

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
                print(f"I2C{bus}:ADDRess:BIT {shift};I2C{bus}:FREQuency {freq:_d};", end="", file=self.stdout)
            else:
                print("", file=self.stdout)
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
                # print("cb_i2c_scan", "Query", param, file=sys.stderr)
                scanned = bus.scan()
                if not scanned:
                    print(BUS_FAIL_CODE, file=self.stdout)
                else:
                    print(",".join([f"{(int(s) << shift):02x}" for s in scanned]), file=self.stdout)
            else:
                self.error_push(E_SYNTAX)
        else:
            self.error_push(E_SYNTAX)

    def cb_i2c_freq(self, param, opt):
        """
        - I2C[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
        - DEFault is 100_000 [Hz]

        :param param:
        :param opt:
        :return:
        """

        query = (opt[-1] == "?")
        bus_number = int(opt[0])
        bus_freq = param
        conf = self.i2c_conf[bus_number]

        if query:
            # print("cb_i2c_freq", bus_number, "Query", param, file=sys.stderr)

            if self.kw_def.match(param).match:
                bus_freq = DEFAULT_I2C_CLOCK
            elif self.kw_max.match(param).match:
                bus_freq = MAX_I2C_CLOCK
            elif self.kw_min.match(param).match:
                bus_freq = MIN_I2C_CLOCK
            else:
                bus_freq = conf.freq
            print(f"{bus_freq:_d}", file=self.stdout)
        elif bus_freq is not None:
            # print("cb_i2c_freq", bus_number, param, file=sys.stderr)

            if self.kw_def.match(bus_freq).match:
                bus_freq = DEFAULT_I2C_CLOCK
            elif self.kw_max.match(param).match:
                bus_freq = MAX_I2C_CLOCK
            elif self.kw_min.match(param).match:
                bus_freq = MIN_I2C_CLOCK
            else:
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
            # print("cb_i2c_address_bit", "Query", param, file=sys.stderr)

            bit = conf.bit
            print(f"{bit}", file=self.stdout)
        elif bit is not None:
            # print("cb_i2c_address_bit", param, file=sys.stderr)
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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]) *, *(([0-9a-fA-F][0-9a-fA-F])+) *, *([01])$")

        if query:
            # print("cb_i2c_write", "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_i2c_write", param, file=sys.stderr)
            searched = rstring.search(param)
            if searched is not None:
                address, data, _, stop = searched.groups()
                stop = bool(int(stop))
                address = int(f"0x{address}", 16) >> shift
                data_array = int(f"0x{data}", 16).to_bytes(ceil(len(data) / 2), "big")
                # print(f"0x{address:02x}", [f"0x{c:02x}" for c in data_array], stop, file=sys.stderr)
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
        rstring = re.compile(r"^([1-9a-fA-F][0-9a-fA-F]) *, *([1-9]|[1-9][0-9]+) *, *([01])$")

        if query:
            # print("cb_i2c_read", "Query", param, file=sys.stderr)
            if param is not None:
                # print("cb_i2c_read", param, file=sys.stderr)

                searched = rstring.search(param)
                if searched is not None:
                    address, length, stop = searched.groups()
                    stop = bool(int(stop))
                    address = int(f"0x{address}", 16) >> shift
                    # print(f"0x{address:02x}", length, stop, file=sys.stderr)
                    try:
                        read = bus.readfrom(int(address), int(length), stop)
                        data = ",".join(f"{d:02x}" for d in read)
                        print(data, file=self.stdout)
                        return
                    except OSError:
                        self.error_push(E_I2C_FAIL)
                        print(BUS_FAIL_CODE, file=self.stdout)
                else:
                    self.error_push(E_INVALID_PARAMETER)
            else:
                self.error_push(E_MISSING_PARAM)
        else:
            self.error_push(E_SYNTAX)
            print(BUS_FAIL_CODE, file=self.stdout)

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
        rstring = re.compile(
            r"^([1-9a-fA-F][0-9a-fA-F]) *, *(([0-9a-fA-F][0-9a-fA-F])+) *, *([0-9a-fA-F]+) *, *([12])$")

        if query:
            # print("cb_i2c_write_memory", "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_i2c_write_memory", param, file=sys.stderr)

            searched = rstring.search(param)

            if searched is not None:
                address, memaddress, _, data, addrsize = searched.groups()
                # print(address, memaddress, data, addrsize, file=sys.stderr)

                address = int(f"0x{address}", 16) >> shift
                memaddress = int(f"0x{memaddress}", 16)
                data_array = int(f"0x{data}", 16).to_bytes(ceil(len(data) / 2), "big")
                addrsize = 8 * int(addrsize)
                # print(f"0x{address:02x}", f"0x{memaddress:02x}", [f"0x{c:02x}" for c in data_array], addrsize, file=sys.stderr)
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
        rstring = re.compile(
            r"^([1-9a-fA-F][0-9a-fA-F]) *, *(([0-9a-fA-F][0-9a-fA-F])+) *, *([1-9]|[1-9][0-9]+) *, *([12])$")

        if query:
            # print("cb_i2c_read_memory", "Query", param, file=sys.stderr)

            if param is not None:
                searched = rstring.search(param)
                if searched is not None:
                    address, memaddress, _, length, addrsize = searched.groups()
                    address = int(f"0x{address}", 16) >> shift
                    memaddress = int(f"0x{memaddress}", 16)
                    length = int(f"0x{length}", 16)
                    addrsize = 8 * int(addrsize)

                    try:
                        read = bus.readfrom_mem(address, memaddress, length)
                        data = ",".join(f"{d:02x}" for d in read)
                        print(data, file=self.stdout)
                        return
                    except OSError:
                        self.error_push(E_I2C_FAIL)
                        print(BUS_FAIL_CODE, file=self.stdout)
                else:
                    self.error_push(E_INVALID_PARAMETER)
            else:
                self.error_push(E_MISSING_PARAM)
        else:
            self.error_push(E_SYNTAX)
        print(BUS_FAIL_CODE, file=self.stdout)

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
            # print("cb_adc_read", "Query", param, file=sys.stderr)
            value = adc.read_u16()
            print(f"{value:_d}", file=self.stdout)  # decimal
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
                print(f"SPI{bus}:CSEL:POLarity {cspol};SPI{bus}:FREQuency {freq:_d};SPI{bus}:MODE {mode};", end="",
                      file=self.stdout)
            print("", file=self.stdout)
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
            # print("cb_spi_cs_pol", "Query", param, file=sys.stderr)
            cspol = conf.cspol
            print(cspol, file=self.stdout)
        elif cspol is not None:
            # print("cb_spi_cs_pol", param, file=sys.stderr)
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
            # print("cb_spi_cs_val", "Query", param, file=sys.stderr)
            print(IO_VALUE_STRINGS[int(cs_pin.value() ^ (not cs_pol))], file=self.stdout)
        elif param is not None:
            # print("cb_spi_cs_val", param, file=sys.stderr)
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
            # print("cb_spi_clock_phase", "Query", param, file=sys.stderr)
            print(conf.mode, file=self.stdout)
        elif mode is not None:
            # print("cb_spi_clock_phase", param, file=sys.stderr)
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
        - SPI[01]:FREQuency[?] num|DEFault|MINimum|MAXimum
        - DEFault is 1_000_000 [Hz]

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
            # print("cb_spi_freq", bus_number, "Query", param, file=sys.stderr)
            if self.kw_def.match(param).match:
                bus_freq = DEFAULT_SPI_CLOCK
            elif self.kw_max.match(param).match:
                bus_freq = MAX_SPI_CLOCK
            elif self.kw_min.match(param).match:
                bus_freq = MIN_SPI_CLOCK
            else:
                bus_freq = conf.freq
            print(f"{bus_freq:_d}", file=self.stdout)
        elif bus_freq is not None:
            # print("cb_spi_freq", bus_number, param, file=sys.stderr)
            try:
                if self.kw_def.match(bus_freq).match:
                    bus_freq = DEFAULT_SPI_CLOCK
                elif self.kw_max.match(param).match:
                    bus_freq = MAX_SPI_CLOCK
                elif self.kw_min.match(param).match:
                    bus_freq = MIN_SPI_CLOCK
                else:
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

        rstring = re.compile(
            r"^(([0-9a-fA-F][0-9a-fA-F])+) *, *([oO][nN]|[oO][fF][fF]|[01]) *, *([oO][nN]|[oO][fF][fF]|[01])$")

        if query:
            # print("cb_spi_tx", bus_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_spi_tx", bus_number, param, file=sys.stderr)
            searched = rstring.search(param)
            if searched is not None:
                data, _, pre_cs, post_cs = searched.groups()
                # print(f"0x{data}", file=sys.stderr)
                string_length = len(data)
                data_array = tuple(int(f"0x{data[i:i + 2]}", 16) for i in range(0, string_length, 2))
                length = len(data_array)
                read_data_array = bytearray([0] * length)
                # print([hex(c) for c in data_array], file=sys.stderr)
                try:
                    self.cb_spi_cs_val(pre_cs, [bus_number, ""])
                    bus.write_readinto(bytes(data_array), read_data_array)
                    self.cb_spi_cs_val(post_cs, [bus_number, ""])
                    data = ",".join(f"{d:02x}" for d in read_data_array)
                    print(data, file=self.stdout)
                except OSError:
                    self.error_push(E_SPI_FAIL)
                    print(BUS_FAIL_CODE, file=self.stdout)
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
        rstring = re.compile(
            r"^(([0-9a-fA-F][0-9a-fA-F])+) *, *([oO][nN]|[oO][fF][fF]|[01]) *, *([oO][nN]|[oO][fF][fF]|[01])$")

        if query:
            # print("cb_spi_write", bus_number, "Query", param, file=sys.stderr)
            self.error_push(E_SYNTAX)
        elif param is not None:
            # print("cb_spi_write", bus_number, param, file=sys.stderr)
            searched = rstring.search(param)
            if searched is not None:
                data, _, pre_cs, post_cs = searched.groups()
                # print(f"0x{data}", file=sys.stderr)
                string_length = len(data)
                data_array = (int(f"0x{data[i:i + 2]}", 16) for i in range(0, string_length, 2))
                # print([hex(c) for c in data_array], file=sys.stderr)
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
            r"^([1-9]|[1-9][0-9]+) *, *([0-9a-fA-F][0-9a-fA-F]) *, *([oO][nN]|[oO][fF][fF]|[01]) *, *([oO][nN]|[oO][fF][fF]|[01])$")

        if query:
            # print("cb_spi_read", bus_number, "Query", param, file=sys.stderr)
            searched = rstring.search(param)

            if searched is not None:
                length, mask, pre_cs, post_cs = searched.groups()
                # print(length, mask, file=sys.stderr)
                try:
                    data_array = bytearray([0] * int(length))
                    mask = int(f"0x{mask}", 16)
                    self.cb_spi_cs_val(pre_cs, [bus_number, ""])
                    bus.readinto(data_array, mask)
                    self.cb_spi_cs_val(post_cs, [bus_number, ""])
                    data = ",".join(f"{d:02x}" for d in data_array)
                    print(data, file=self.stdout)
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
