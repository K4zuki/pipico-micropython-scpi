import sys
import re

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List
from collections import namedtuple

rstring = re.compile(r"^(\D+)(\d+)$")


class ScpiKeyword(namedtuple("ScpiKeyword", ["long", "short", "opt"])):
    """
    - long: `str`
    - short: `str`
    - opt: `list(str)`
    - param_callback: `function`
    """

    def __str__(self):
        return self.long

    def match(self, candidate):
        """
        :param str candidate: "XXX" or "XXX123" style string
        :return Boolean:
        """
        short = self.short.upper()
        long = self.long.upper()
        optionval = None
        if isinstance(candidate, str):
            candidate = candidate.upper()
            if self.opt is not None:
                candidate, optionval = re.search(rstring, candidate)

            return candidate.startswith(short) and long.startswith(candidate)
        else:
            return False


ScpiKeyword.__new__.__defaults__ = tuple([None] * 3)


def cb_do_nothing(param="", query=False):
    """Abstract callback function for ScpiCommand class"""
    pass


class ScpiCommand(namedtuple("ScpiCommand", ["keywords", "query", "callback"])):
    """
    - `keywords`: list of `ScpiKeyword`
    - `query`: flag if command is a query
    - `callback`: `function pointer`
    """

    def match(self, candidate_cmd):
        return all([keyword.match(kw_candidate) for keyword, kw_candidate in zip(self.keywords, candidate_cmd)])


kw = ScpiKeyword("KEYWord", "KEYW")


class MicroScpiDevice:
    commands_write = [ScpiCommand((kw, kw), False, cb_do_nothing), ]  # type: List[ScpiCommand]
    commands_query = [ScpiCommand((kw, kw), False, cb_do_nothing), ]  # type: List[ScpiCommand]

    @staticmethod
    def mini_lexer(line: str):
        """ Split `line` into tuple of (list of keywords) and a parameter string

        :param str line: candidate command string
        :return tuple: ([keywords], param)
        """
        line = line.split(";")[0]
        command = line
        param = None

        if " " in line:
            command = line.split()[0]
            param = line.lstrip(command)

        command = command.split(":")
        return command, param

    def parse_and_process(self, line: str):
        """ Parse `line` and process if it is valid

        :param str line: candidate command string
        """
        line = line.strip()
        if len(line) == 0:
            return
        candidate_cmd, candidate_param = self.mini_lexer(line)

        commands = self.commands_query if candidate_cmd[-1].endswith("?") else self.commands_write

        length_matched = [c for c in commands if len(c.keywords) == len(candidate_cmd)]

        if len(length_matched) == 0:
            print("{}: command not found".format(':'.join(candidate_cmd)))
        else:
            candidate_cmd[-1] = candidate_cmd[-1].strip("?")
            for command in length_matched:
                if command.match(candidate_cmd):
                    command.callback(candidate_param, command.query)
                    break
            else:
                # When no break occurred - error
                print("{}: command not found".format(':'.join(candidate_cmd)))
