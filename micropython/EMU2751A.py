"""
DIAGnostic:RELay:CYCLes? <No Param>
DIAGnostic:RELay:CYCLes:CLEar <No Param>
ROUTe:CLOSe (@101)
ROUTe:CLOSe? (@101)
ROUTe:OPEN (@101)
ROUTe:OPEN? (@101)
SYSTem:CDEScription? <No Param>
SYSTem:ERRor? <No Param>
SYSTem:VERSion? <No Param>
*CLS <No Param>
*ESE/*ESE? <No Param>
*ESR? <No Param>
*IDN? <No Param>
*OPC/*OPC? <No Param>
*RST <No Param>
*SRE/*SRE? <No Param>
*STB? <No Param>
*TST? <No Param>
"""
from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice


class EMU2751A(MicroScpiDevice):
    kw_route = ScpiKeyword("ROUTe", "ROUT")
    kw_close = ScpiKeyword("CLOSe", "CLOS")
    kw_open = ScpiKeyword("OPEN", "OPEN")
    kw_diag = ScpiKeyword("DIAGnostic", "DIAG")
    kw_relay = ScpiKeyword("RELay", "REL")
    kw_cycles = ScpiKeyword("CYCLes", "CYCL")
    kw_clear = ScpiKeyword("CLEar", "CLE")
    kw_system = ScpiKeyword("SYSTem", "SYST")
    kw_cdescription = ScpiKeyword("CDEScription", "CDES")
    kw_error = ScpiKeyword("ERRor", "ERR")
    kw_version = ScpiKeyword("VERSion", "VERS")
    kw_cls = ScpiKeyword("*CLS", "*CLS")
    kw_ese = ScpiKeyword("*ESE", "*ESE")
    kw_esr = ScpiKeyword("*ESR", "*ESR")
    kw_idn = ScpiKeyword("*IDN", "*IDN")
    kw_opc = ScpiKeyword("*OPC", "*OPC")
    kw_rst = ScpiKeyword("*RST", "*RST")
    kw_sre = ScpiKeyword("*SRE", "*SRE")
    kw_stb = ScpiKeyword("*STB", "*STB")
    kw_tst = ScpiKeyword("*TST", "*TST")

    def __init__(self):
        super().__init__()

        diagnostic_relay_cycles = ScpiCommand((self.kw_diag, self.kw_relay, self.kw_cycles), self.cb_loopback)
        diagnostic_relay_cycles_clear = ScpiCommand((self.kw_diag, self.kw_relay, self.kw_cycles, self.kw_clear),
                                                    self.cb_loopback)
        route_close = ScpiCommand((self.kw_route, self.kw_close), self.cb_loopback)
        route_open = ScpiCommand((self.kw_route, self.kw_open), self.cb_loopback)
        system_description = ScpiCommand((self.kw_system, self.kw_cdescription), self.cb_loopback)
        system_error = ScpiCommand((self.kw_system, self.kw_error), self.cb_loopback)
        system_version = ScpiCommand((self.kw_system, self.kw_version), self.cb_loopback)
        cls = ScpiCommand((self.kw_cls,), self.cb_loopback)
        ese = ScpiCommand((self.kw_ese,), self.cb_loopback)
        opc = ScpiCommand((self.kw_opc,), self.cb_loopback)
        rst = ScpiCommand((self.kw_rst,), self.cb_loopback)
        sre = ScpiCommand((self.kw_sre,), self.cb_loopback)
        ese_q = ScpiCommand((self.kw_ese,), self.cb_loopback)
        esr_q = ScpiCommand((self.kw_esr,), self.cb_loopback)
        idn_q = ScpiCommand((self.kw_idn,), self.cb_idn)
        opc_q = ScpiCommand((self.kw_opc,), self.cb_loopback)
        sre_q = ScpiCommand((self.kw_sre,), self.cb_loopback)
        stb_q = ScpiCommand((self.kw_stb,), self.cb_loopback)
        tst_q = ScpiCommand((self.kw_tst,), self.cb_loopback)

        self.commands_write = [cls, ese, opc, rst, sre,
                               route_close, route_open,
                               diagnostic_relay_cycles_clear]
        self.commands_query = [ese_q, esr_q, idn_q, opc_q, sre_q,
                               route_close, route_open,
                               diagnostic_relay_cycles,
                               system_description, system_error, system_version]

    @staticmethod
    def cb_loopback(param=""):
        if param is not None:
            print(str(param))
        else:
            print("no parameter given")

    @staticmethod
    def cb_idn(param=""):
        """<Vendor name>,<Model number>,<Serial number>,<Firmware version>"""
        print("MicroScpiDevice,EMU2751A,C0FEE,0.0.1")
