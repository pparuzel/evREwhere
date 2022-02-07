'''Printers module'''

from itertools import cycle
from evrewhere.colors import COLORS, Fore, Style
from evrewhere.file_match import FileMatch

class VerbosePrinter:
    '''Regular printer that shows the result object'''
    def print(self, result: FileMatch, *args: str, **kwargs):
        '''Printing function'''
        print(result, *args, **kwargs)


class FileInfoPrefixFormat:
    '''Provides colored formats for file info prefixes'''
    def __init__(self, *,
        with_filename: bool = False,
        with_lineno: bool = False,
    ):
        self.filename_format: str = (
            f'{Fore.MAGENTA}' + '{path}' + f'{Fore.CYAN}:'
            if with_filename else
            ''
        )
        self.linenumber_format: str = (
            f'{Fore.GREEN}' + '{lineno}' + f'{Fore.CYAN}:'
            if with_lineno else
            ''
        )

    def prefixes(self, path: str, lineno: int) -> str:
        '''Returns prefixes for the FileMatch'''
        return (
            # File path part
            self.filename_format.format(path=path) +
            # Line number part
            self.linenumber_format.format(lineno=lineno) +
            # Drop all styles
            Style.RESET_ALL
        )


class FileInfoPrefixPrinter(FileInfoPrefixFormat):
    '''Prints colored filename and line number prefixes'''
    def print(self, path: str, lineno: int, *args: str, **kwargs):
        '''Printing function'''
        print(
            self.prefixes(path, lineno),
            *args,
            **kwargs,
        )


class MatchPrinter(FileInfoPrefixFormat):
    '''Sophisticated printer that handles prefixes and templates'''
    def __init__(self, template: str, group_count: int, *,
        with_filename: bool = False,
        with_lineno: bool = False,
        full_lines: bool = False
    ):
        super().__init__(with_filename=with_filename, with_lineno=with_lineno)
        self.template = template or '{0}'
        self.group_count = group_count
        self.full_lines = full_lines
        if template is None or group_count > 0:
            self.process_match = self.__process_match_colored
        else:
            self.process_match = self.__process_match_template

    def __process_match_template(self, result: FileMatch) -> str:
        return self.template.format(result.match.group(0), *result.match.groups(), **COLORS)

    def __process_match_colored(self, result: FileMatch) -> str:
        color = cycle(COLORS.values())
        output = ''
        last_end = 0
        if self.full_lines:
            fullmatch = result.line
            offset = result.line_offset
        else:
            fullmatch = result.match.group(0)
            offset = result.match.span()[0]
        # Must be defined when captures are searched but not found
        end = 0
        for i in range(self.group_count):
            if not result.match.group(i + 1):
                continue
            # Wrap captures with colors
            start = result.match.start(i + 1) - offset
            end = result.match.end(i + 1) - offset
            output += fullmatch[last_end:start] + Style.BRIGHT + next(color)
            output += fullmatch[start:end] + Style.RESET_ALL
            last_end = end
        output += fullmatch[end:] + Style.RESET_ALL
        return output

    def print(self, result: FileMatch, *args, **kwargs):
        '''Printing function'''
        print(
            self.prefixes(result.path, result.lineno) +
            self.process_match(result),
            *args,
            **kwargs
        )
