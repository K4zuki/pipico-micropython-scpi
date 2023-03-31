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

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List

import re
from collections import namedtuple

import machine

from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice, cb_do_nothing
from GpakMux import GpakMux


class RaspberryScpiPico(MicroScpiDevice):
    kw_cls = ScpiKeyword("*CLS", "*CLS")
    kw_ese = ScpiKeyword("*ESE", "*ESE")
    kw_esr = ScpiKeyword("*ESR", "*ESR")
    kw_idn = ScpiKeyword("*IDN", "*IDN")
    kw_opc = ScpiKeyword("*OPC", "*OPC")
    kw_rst = ScpiKeyword("*RST", "*RST")
    kw_sre = ScpiKeyword("*SRE", "*SRE")
    kw_stb = ScpiKeyword("*STB", "*STB")
    kw_tst = ScpiKeyword("*TST", "*TST")

    kw_machine = ScpiKeyword("MACHINE", "MACHINE")
    kw_pin = ScpiKeyword("PIN", "PIN", ["6", "7", "14", "15", "20", "21", "22"])
    kw_pwm = ScpiKeyword("PWM", "PWM")
    kw_duty = ScpiKeyword("DUTY", "DUTY")
    kw_on = ScpiKeyword("ON", "ON")
    kw_off = ScpiKeyword("OFF", "OFF")
    kw_uart = ScpiKeyword("UART", "UART")
    kw_baud = ScpiKeyword("BAUDrate", "BAUD")
    kw_parity = ScpiKeyword("PARITY", "PARITY")
    kw_width = ScpiKeyword("WIDTH", "WIDTH")
    kw_start = ScpiKeyword("START", "START")
    kw_stop = ScpiKeyword("STOP", "STOP")
    kw_i2c = ScpiKeyword("I2C", "I2C", ["0", "1"])
    kw_scan = ScpiKeyword("SCAN", "SCAN")
    kw_addr = ScpiKeyword("ADDRess", "ADDR")
    kw_bit = ScpiKeyword("BIT", "BIT")
    kw_freq = ScpiKeyword("FREQuency", "FREQ")
    kw_spi = ScpiKeyword("SPI", "SPI", ["0", "1"])
    kw_csel = ScpiKeyword("CSEL", "CS")
    kw_mode = ScpiKeyword("MODE", "MODE")
    kw_pol = ScpiKeyword("POLarity", "POL")
    kw_xfer = ScpiKeyword("TRANSfer", "TRANS")
    kw_adc = ScpiKeyword("ADC", "ADC", ["0", "1", "2"])
    kw_high = ScpiKeyword("HIGH", "HIGH")
    kw_low = ScpiKeyword("LOW", "LOW")
    kw_write = ScpiKeyword("WRITE", "WRITE")
    kw_read = ScpiKeyword("READ", "READ")
    kw_value = ScpiKeyword("VALue", "VALue")

    def __init__(self, mux):
        super().__init__()
        self.mux = mux  # type: GpakMux
        self.mux.disconnect_all()

        cls = ScpiCommand((self.kw_cls,), False, cb_do_nothing)
        ese = ScpiCommand((self.kw_ese,), False, cb_do_nothing)
        opc = ScpiCommand((self.kw_opc,), False, cb_do_nothing)
        rst = ScpiCommand((self.kw_rst,), False, cb_do_nothing)
        sre = ScpiCommand((self.kw_sre,), False, cb_do_nothing)
        ese_q = ScpiCommand((self.kw_ese,), True, cb_do_nothing)
        esr_q = ScpiCommand((self.kw_esr,), True, cb_do_nothing)
        idn_q = ScpiCommand((self.kw_idn,), True, self.cb_idn)
        opc_q = ScpiCommand((self.kw_opc,), True, cb_do_nothing)
        sre_q = ScpiCommand((self.kw_sre,), True, cb_do_nothing)
        stb_q = ScpiCommand((self.kw_stb,), True, cb_do_nothing)
        tst_q = ScpiCommand((self.kw_tst,), True, cb_do_nothing)

        machine_freq = ScpiCommand((self.kw_machine, self.kw_freq), False, cb_do_nothing)

        pin_mode = ScpiCommand((self.kw_pin, self.kw_mode), False, cb_do_nothing)
        pin_val = ScpiCommand((self.kw_pin, self.kw_value), False, cb_do_nothing)
        pin_on = ScpiCommand((self.kw_pin, self.kw_on), False, cb_do_nothing)
        pin_off = ScpiCommand((self.kw_pin, self.kw_off), False, cb_do_nothing)

        pwm_freq = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_freq), False, cb_do_nothing)
        pwm_duty = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_duty), False, cb_do_nothing)

        i2c_freq = ScpiCommand((self.kw_i2c, self.kw_freq), False, cb_do_nothing)
        i2c_abit = ScpiCommand((self.kw_i2c, self.kw_addr, self.kw_bit), False, cb_do_nothing)
        i2c_write = ScpiCommand((self.kw_i2c, self.kw_write), False, cb_do_nothing)

        spi_cpol = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_pol), False, cb_do_nothing)
        spi_mode = ScpiCommand((self.kw_spi, self.kw_mode), False, cb_do_nothing)
        spi_freq = ScpiCommand((self.kw_spi, self.kw_freq), False, cb_do_nothing)

        machine_freq_q = ScpiCommand((self.kw_machine, self.kw_freq), True, cb_do_nothing)

        pin_mode_q = ScpiCommand((self.kw_pin, self.kw_mode), True, cb_do_nothing)
        pin_val_q = ScpiCommand((self.kw_pin, self.kw_value), True, cb_do_nothing)

        pwm_freq_q = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_freq), True, cb_do_nothing)
        pwm_duty_q = ScpiCommand((self.kw_pin, self.kw_pwm, self.kw_duty), True, cb_do_nothing)

        i2c_scan = ScpiCommand((self.kw_i2c, self.kw_scan), True, cb_do_nothing)
        i2c_freq_q = ScpiCommand((self.kw_i2c, self.kw_freq), True, cb_do_nothing)
        i2c_abit_q = ScpiCommand((self.kw_i2c, self.kw_addr, self.kw_bit), True, cb_do_nothing)
        i2c_read_q = ScpiCommand((self.kw_i2c, self.kw_read), True, cb_do_nothing)

        spi_cpol_q = ScpiCommand((self.kw_spi, self.kw_csel, self.kw_pol), True, cb_do_nothing)
        spi_mode_q = ScpiCommand((self.kw_spi, self.kw_mode), True, cb_do_nothing)
        spi_freq_q = ScpiCommand((self.kw_spi, self.kw_freq), True, cb_do_nothing)

        adc_read_q = ScpiCommand((self.kw_adc, self.kw_read), True, cb_do_nothing)

        self.commands_write = [cls, ese, opc, rst, sre,
                               machine_freq,
                               pin_mode, pin_val, pin_on, pin_off,
                               pwm_freq, pwm_duty,
                               i2c_scan, i2c_freq, i2c_abit, i2c_write,
                               spi_cpol, spi_mode, spi_freq,
                               ]
        self.commands_query = [ese_q, esr_q, idn_q, opc_q, sre_q, stb_q, tst_q,
                               machine_freq_q,
                               pin_mode_q, pin_val_q,
                               pwm_freq_q, pwm_duty_q,
                               i2c_freq_q, i2c_abit_q, i2c_read_q,
                               spi_cpol_q, spi_mode_q, spi_freq_q,
                               adc_read_q,
                               ]

    @staticmethod
    def cb_idn(param="", query=False):
        """<Vendor name>,<Model number>,<Serial number>,<Firmware version>"""
        serial = machine.unique_id()
        print(f"RaspberryPiPico,RP001,{serial},0.0.1")

    @staticmethod
    def cb_version(param="", query=False):
        """The command returns a string in the form of “YYYY.V”, where “YYYY” represents
        the year of the version and “V” represents a version for that year (e.g. 1997.0).
        """
        print("2023.04")
