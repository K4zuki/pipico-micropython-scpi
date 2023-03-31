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

import machine

from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice, cb_do_nothing

ABS_MAX_CLOCK = 275_000_000
ABS_MIN_CLOCK = 100_000_000


class RaspberryScpiPico(MicroScpiDevice):
    kw_cls = ScpiKeyword("*CLS", "*CLS", None)
    kw_ese = ScpiKeyword("*ESE", "*ESE", None)
    kw_esr = ScpiKeyword("*ESR", "*ESR", None)
    kw_idn = ScpiKeyword("*IDN", "*IDN", None)
    kw_opc = ScpiKeyword("*OPC", "*OPC", None)
    kw_rst = ScpiKeyword("*RST", "*RST", None)
    kw_sre = ScpiKeyword("*SRE", "*SRE", None)
    kw_stb = ScpiKeyword("*STB", "*STB", None)
    kw_tst = ScpiKeyword("*TST", "*TST", None)

    kw_machine = ScpiKeyword("MACHINE", "MACHINE", None)
    kw_pin = ScpiKeyword("PIN", "PIN", ["6", "7", "14", "15", "20", "21", "22"])
    kw_pwm = ScpiKeyword("PWM", "PWM", None)
    kw_duty = ScpiKeyword("DUTY", "DUTY", None)
    kw_on = ScpiKeyword("ON", "ON", None)
    kw_off = ScpiKeyword("OFF", "OFF", None)
    kw_uart = ScpiKeyword("UART", "UART", None)
    kw_baud = ScpiKeyword("BAUDrate", "BAUD", None)
    kw_parity = ScpiKeyword("PARITY", "PARITY", None)
    kw_width = ScpiKeyword("WIDTH", "WIDTH", None)
    kw_start = ScpiKeyword("START", "START", None)
    kw_stop = ScpiKeyword("STOP", "STOP", None)
    kw_i2c = ScpiKeyword("I2C", "I2C", ["0", "1"])
    kw_scan = ScpiKeyword("SCAN", "SCAN", None)
    kw_addr = ScpiKeyword("ADDRess", "ADDR", None)
    kw_bit = ScpiKeyword("BIT", "BIT", None)
    kw_freq = ScpiKeyword("FREQuency", "FREQ", None)
    kw_spi = ScpiKeyword("SPI", "SPI", ["0", "1"])
    kw_csel = ScpiKeyword("CSEL", "CS", None)
    kw_mode = ScpiKeyword("MODE", "MODE", None)
    kw_pol = ScpiKeyword("POLarity", "POL", None)
    kw_xfer = ScpiKeyword("TRANSfer", "TRANS", None)
    kw_adc = ScpiKeyword("ADC", "ADC", ["0", "1", "2"])
    kw_high = ScpiKeyword("HIGH", "HIGH", None)
    kw_low = ScpiKeyword("LOW", "LOW", None)
    kw_write = ScpiKeyword("WRITE", "WRITE", None)
    kw_read = ScpiKeyword("READ", "READ", None)
    kw_value = ScpiKeyword("VALue", "VALue", None)

    def __init__(self):
        super().__init__()

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

        machine_freq = ScpiCommand((self.kw_machine, self.kw_freq), False, self.cb_machine_freq)

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

        machine_freq_q = ScpiCommand((self.kw_machine, self.kw_freq), True, self.cb_machine_freq)

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

    @staticmethod
    def cb_machine_freq(param="", query=False):
        """

        :return:
        """

        machine_freq = param

        if query is True:
            machine_freq = machine.freq()
            print(f"{machine_freq}")
        else:
            assert machine_freq is not None
            machine_freq = int(machine_freq)
            assert ABS_MIN_CLOCK < machine_freq < ABS_MAX_CLOCK
            assert isinstance(machine_freq, int)
            machine.freq(machine_freq)
