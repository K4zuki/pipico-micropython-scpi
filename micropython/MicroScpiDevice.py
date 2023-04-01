import sys
import re

if sys.version_info > (3, 6, 0):
    from typing import Tuple, List
from collections import namedtuple

rstring = re.compile(r"^(\D+)(\d+|\?)$")


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


class ScpiMatch(namedtuple("ScpiMatch", ["match", "opt"])):
    pass


def cb_do_nothing(*args, **kwargs):
    """Abstract callback function for ScpiCommand class
    """
    pass


class ScpiCommand(namedtuple("ScpiCommand", ["keywords", "query", "callback"])):
    """
    - `keywords`: list of `ScpiKeyword`
    - `query`: flag if command is a query
    - `callback`: `function pointer`
    """

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


class MicroScpiDevice:
    commands = [ScpiCommand((kw, kw), False, cb_do_nothing), ]  # type: List[ScpiCommand]

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
            print("{}: command not found".format(':'.join(candidate_cmd)))
        else:
            for command in length_matched:
                result = command.match(candidate_cmd)
                if result.match is True:
                    command.callback(candidate_param, result.opt)
                    break
            else:
                # When no break occurred - error
                print("{}: command not found".format(':'.join(candidate_cmd)))
