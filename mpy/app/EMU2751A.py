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
import sys

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List

import re
from collections import namedtuple

from MicroScpiDevice import ScpiKeyword, ScpiCommand, MicroScpiDevice, cb_do_nothing
from GpakMux import GpakMux


class CrossBars(namedtuple("CrossBars", ["range", "start", "end", "single"])):
    """
    - range: crossbar id range
    - start: crossbar start id
    - end: crossbar end id inclusive
    - single: crossbar id
    """
    CROSSBAR_MIN = 101
    CROSSBAR_MAX = 206
    CROSSBARS = (101, 102, 103, 104, 105, 106, 201, 202, 203, 204, 205, 206)

    def update(self):
        _single = self.CROSSBAR_MIN
        _start = self.CROSSBAR_MIN
        _end = self.CROSSBAR_MAX
        _range = None
        if self.range is not None:
            _single = self.single
            _range = self.range
            if self.start is not None:
                start = int(self.start)
                if not self.CROSSBAR_MIN <= start <= self.CROSSBAR_MAX:
                    print("Error:", start)
                _start = min(_end, max(start, self.CROSSBAR_MIN))
            if self.end is not None:
                end = int(self.end)
                if not self.CROSSBAR_MIN <= end <= self.CROSSBAR_MAX:
                    print("Error:", end)
                _end = max(_start, min(end, self.CROSSBAR_MAX))
            assert _start <= _end
            _range = tuple(xb for xb in range(_start, _end + 1) if xb in self.CROSSBARS)
        elif self.single is not None:
            _start = self.start
            _end = self.end
            single = int(self.single)
            if not (self.CROSSBAR_MAX >= single >= self.CROSSBAR_MIN):
                print("Error:", self.single)
                _single = self.CROSSBAR_MAX if single > self.CROSSBAR_MAX else min(single, self.CROSSBAR_MIN)
            else:
                _single = single
            _range = (single,)

        return CrossBars(_range, _start, _end, _single)


class EMU2751A(MicroScpiDevice):
    kw_route = ScpiKeyword("ROUTe", "ROUT", None)
    kw_close = ScpiKeyword("CLOSe", "CLOS", ["?"])
    kw_open = ScpiKeyword("OPEN", "OPEN", ["?"])
    kw_diag = ScpiKeyword("DIAGnostic", "DIAG", ["?"])
    kw_relay = ScpiKeyword("RELay", "REL", None)
    kw_cycles = ScpiKeyword("CYCLes", "CYCL", ["?"])
    kw_clear = ScpiKeyword("CLEar", "CLE", None)
    kw_system = ScpiKeyword("SYSTem", "SYST", None)
    kw_cdescription = ScpiKeyword("CDEScription", "CDES", ["?"])
    kw_error = ScpiKeyword("ERRor", "ERR", ["?"])
    kw_version = ScpiKeyword("VERSion", "VERS", ["?"])
    bus = None
    mux = None
    relay_counter = 0

    def __init__(self, mux):
        super().__init__()
        self.mux = mux  # type: GpakMux
        self.mux.disconnect_all()

        diagnostic_relay_cycles = ScpiCommand((self.kw_diag, self.kw_relay, self.kw_cycles), True, cb_do_nothing)
        diagnostic_relay_cycles_clear = ScpiCommand((self.kw_diag, self.kw_relay, self.kw_cycles, self.kw_clear),
                                                    False, cb_do_nothing)
        route_close = ScpiCommand((self.kw_route, self.kw_close), False, self.cb_relay_close)
        route_open = ScpiCommand((self.kw_route, self.kw_open), False, self.cb_relay_open)
        system_description = ScpiCommand((self.kw_system, self.kw_cdescription), False, cb_do_nothing)
        system_error = ScpiCommand((self.kw_system, self.kw_error), False, cb_do_nothing)
        system_version = ScpiCommand((self.kw_system, self.kw_version), False, self.cb_version)
        cls = ScpiCommand((self.kw_cls,), False, cb_do_nothing)
        ese = ScpiCommand((self.kw_ese,), False, cb_do_nothing)
        opc = ScpiCommand((self.kw_opc,), False, cb_do_nothing)
        rst = ScpiCommand((self.kw_rst,), False, cb_do_nothing)
        sre = ScpiCommand((self.kw_sre,), False, cb_do_nothing)
        esr_q = ScpiCommand((self.kw_esr,), True, cb_do_nothing)
        idn_q = ScpiCommand((self.kw_idn,), True, self.cb_idn)
        stb_q = ScpiCommand((self.kw_stb,), True, cb_do_nothing)
        tst_q = ScpiCommand((self.kw_tst,), True, cb_do_nothing)

        self.commands = [cls, ese, opc, rst, sre, esr_q, idn_q, stb_q, tst_q,
                         diagnostic_relay_cycles, diagnostic_relay_cycles_clear,
                         route_close, route_open,
                         system_description, system_error,
                         system_version,
                         ]

    rstring = re.compile(r"((\d..)?:(\d..)?),?|(\d..),?")

    def channel_parser(self, param="(@101)"):
        param = param.strip()
        crossbars = []  # type: List[CrossBars]
        if not isinstance(param, str):
            print("Error: No parameter given")
            return
        elif not (param.startswith("(@") and param.endswith(")")):
            print("Error: Wrong parameter string: '{}'".format(param))
            return
        else:
            param = param.strip("(@)")
            start = 0
            end = len(param)
            while start < end:
                param = param[start:]
                rs = re.search(self.rstring, param)
                if rs is None:
                    break
                else:
                    print(rs.groups())
                    crossbar = CrossBars(*rs.groups())
                    crossbar = crossbar.update()
                    crossbars.append(crossbar)
                    start = rs.end()
                    self.relay_counter += 1
            return crossbars

    def cb_relay_close(self, param, opt):
        query = (opt[-1] == "?")

        if query:
            print("cb_relay_close", "Query", param)
        elif param is not None:
            print("cb_relay_close", param)

            param = param.strip()
            crossbars = self.channel_parser(param)
            if crossbars is not None:
                stat = []
            for crossbar in crossbars:
                for cross in crossbar.range:
                    rowcol = self.mux.int_to_rowcol(cross)
                    if query is True:
                        stat.append(str(self.mux.query(*rowcol)))
                    else:
                        self.mux.connect(*rowcol)
                print("Close:", "?" if query is True else "-", crossbar.range)
            print("{}".format(",".join(stat)))
        else:
            print("syntax error: no parameter")

    def cb_relay_open(self, param, opt):
        query = (opt[-1] == "?")

        if query:
            print("cb_relay_open", "Query", param)
        elif param is not None:
            print("cb_relay_open", param)

            param = param.strip()
            crossbars = self.channel_parser(param)
            if crossbars is not None:
                stat = []
                for crossbar in crossbars:
                    for cross in crossbar.range:
                        rowcol = self.mux.int_to_rowcol(cross)
                        if query is True:
                            stat.append("0" if self.mux.query(*rowcol) == 1 else "1")
                        else:
                            self.mux.disconnect(*rowcol)
                    print("Open:", "?" if query is True else "-", crossbar.range)
                print("{}".format(",".join(stat)))
        else:
            print("syntax error: no parameter")

    @staticmethod
    def cb_idn(param="", query=False):
        """<Vendor name>,<Model number>,<Serial number>,<Firmware version>"""
        print("MicroScpiDevice,EMU2751A,C0FEE,0.0.2")

    @staticmethod
    def cb_version(param="", query=False):
        """The command returns a string in the form of “YYYY.V”, where “YYYY” represents
        the year of the version and “V” represents a version for that year (e.g. 1997.0).
        """
        print("2023.04")
