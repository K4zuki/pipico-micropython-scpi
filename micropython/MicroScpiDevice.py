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
import sys
import re

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List
from collections import namedtuple

rstring = re.compile(r"^(\*?[a-zA-Z]\w+[a-zA-Z])(\d+|\?)$")


class ScpiKeyword(namedtuple("ScpiKeyword", [
    "long",  # [str] Long form string
    "short",  # [str] Short form string
    "opt"  # [list(str)] list of option strings
])):
    """
    - long: `str`
    - short: `str`
    - opt: `list(str)`
    """

    def __str__(self):
        return self.long

    def match(self, candidate):
        """
        :param str candidate: keyword string. may have option string either numeric or "?".
            i.e. "XXX" or "XXX123" or "XXX?" style
        :return ScpiMatch:
        """
        short = self.short.upper()
        long = self.long.upper()
        optionval = None
        matched = False
        if isinstance(candidate, str):
            candidate = candidate.upper()
            if self.opt is not None:
                search = re.search(rstring, candidate)
                if search is not None:
                    candidate, optionval = search.groups()
                if "?" in self.opt and optionval != "?":
                    matched = candidate.startswith(short) and long.startswith(candidate)
                else:
                    matched = (str(optionval) in self.opt) and candidate.startswith(
                        short) and long.startswith(candidate)
            else:
                matched = candidate.startswith(short) and long.startswith(candidate)

            return ScpiMatch(matched, optionval)
        else:
            return ScpiMatch(False, optionval)


class ScpiMatch(namedtuple("ScpiMatch", [
    "match",  # [bool] matched flag
    "opt"  # [str] option string
])):
    """
    - match: `bool`
    - opt: `str`
    """
    pass


class ScpiErrorNumber(namedtuple("ScpiErrorNumber", [
    "id",  # [int] Error number
    "message"  # [str] Error message
])):
    """
    - id: `int`
    - message: `str`
    """
    pass


def cb_do_nothing(*args, **kwargs):
    """Abstract callback function for ScpiCommand class
    """
    print("cb_do_nothing")


class ScpiCommand(namedtuple("ScpiCommand", [
    "keywords",  # list of `ScpiKeyword`
    "query",  # flag if command is a query
    "callback"  # function pointer
])):
    """
    - `keywords`: list of `ScpiKeyword`
    - `query`: flag if command is a query
    - `callback`: `function pointer`
    """

    def cat(self):
        return ":".join([k.long for k in self.keywords])

    def match(self, candidate_cmd):
        """ Tests if `candidate_cmd` matches with `keywords`.

        `len(candidate_cmd)` must match with `len(keywords)`

        :param List[str] candidate_cmd: candidate command
        :return:
        """

        keywords = self.keywords  # type:List[ScpiKeyword]

        results = [keyword.match(kw_candidate) for keyword, kw_candidate in zip(keywords, candidate_cmd)]
        matched = all([result.match for result in results])
        options = [result.opt for result in results]
        return ScpiMatch(matched, options)


kw = ScpiKeyword("KEYWord", "KEYW", None)

E_NONE = ScpiErrorNumber(0, "No error")
E_SYNTAX = ScpiErrorNumber(-102, "Syntax error")

MAX_ERROR_COUNT = 256
ERROR_LIST = [E_NONE] * MAX_ERROR_COUNT


class MicroScpiDevice:
    kw_cls = ScpiKeyword("*CLS", "*CLS", None)
    kw_ese = ScpiKeyword("*ESE", "*ESE", ["?"])
    kw_esr = ScpiKeyword("*ESR", "*ESR", ["?"])
    kw_idn = ScpiKeyword("*IDN", "*IDN", ["?"])
    kw_opc = ScpiKeyword("*OPC", "*OPC", ["?"])
    kw_rst = ScpiKeyword("*RST", "*RST", None)
    kw_sre = ScpiKeyword("*SRE", "*SRE", ["?"])
    kw_stb = ScpiKeyword("*STB", "*STB", ["?"])
    kw_tst = ScpiKeyword("*TST", "*TST", ["?"])
    commands = [ScpiCommand((kw, kw), False, cb_do_nothing), ]  # type: List[ScpiCommand]

    error_rd_pointer = 0
    error_wr_pointer = 0
    error_counter = 0

    def error_push(self, error_no):
        ERROR_LIST[self.error_wr_pointer] = error_no
        self.error_counter += 1
        self.error_wr_pointer = (self.error_wr_pointer + 1) & 0xFF

    @staticmethod
    def mini_lexer(line: str):
        """ Split `line` into tuple of (list of keywords) and a parameter string

        :param str line: candidate command string
        :return tuple: ([keywords], param)
        """
        lexer_rstring = re.compile(r"^(([\w:?\*]+)\s?([\w.,]+)?);?")

        search = lexer_rstring.search(line)
        if search is not None:
            processed_line = search.groups()
            line, command, param = processed_line

            command = command.split(":")
            return command, param
        else:
            return "", ""

    def parse_and_process(self, line: str):
        """ Parse `line` and process if it is valid

        :param str line: candidate command string
        """
        line = line.strip()
        if len(line) == 0:
            return
        candidate_cmd, candidate_param = self.mini_lexer(line)

        commands = self.commands

        length_matched = [c for c in commands if len(c.keywords) == len(candidate_cmd)]  # type: List[ScpiCommand]

        if len(length_matched) == 0:
            self.error_push(E_SYNTAX)
            # print("{}: command not found".format(':'.join(candidate_cmd)))
        else:
            for command in length_matched:
                result = command.match(candidate_cmd)
                if result.match is True:
                    command.callback(candidate_param, result.opt)
                    break
            else:
                # When no break occurred - error
                self.error_push(E_SYNTAX)
                # print("{}: command not found".format(':'.join(candidate_cmd)))
