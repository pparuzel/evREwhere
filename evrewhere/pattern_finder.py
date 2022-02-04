'''Pattern Finder module'''

from typing import Callable, Union, Iterable, List, IO

import os
import re
import sys
import pathlib
from evrewhere import FileMatch
from evrewhere.colors import Fore, Style


def create_pattern(pattern_string: str, *,
    case_insensitive: re.RegexFlag = None,
    dot_all: re.RegexFlag = None
) -> re.Pattern:
    '''Convert a pattern string into regex Pattern object'''
    flags = re.MULTILINE
    flags |= dot_all or 0
    flags |= case_insensitive or 0
    return re.compile(pattern_string, flags)


def limited(seq: Iterable, limit: int):
    '''Generate a limited number of results'''
    for i, value in enumerate(seq):
        if i >= limit:
            break
        yield value


class PatternFinder:
    '''File and directory search engine based on supplied regex pattern'''
    def __init__(
        self,
        pattern: Union[re.Pattern, str], *,  # pylint: disable=E1136
        limit: int = 0,
        line_numbers: bool = False,
        case_insensitive: bool = False,
        dot_all: bool = False,
        full_lines: bool = False
    ):
        self.pattern: re.Pattern = (
            create_pattern(
                pattern,
                case_insensitive=re.IGNORECASE if case_insensitive else None,
                dot_all=re.DOTALL if dot_all else None
            )
            if isinstance(pattern, str) else
            pattern
        )
        self.limit: int = limit
        self.results: List[FileMatch] = []
        self.count_lineno: bool = line_numbers
        self.match_handler: Callable[[str, int, int, FileMatch], bool] = \
            PatternFinder.default_match_handler
        if full_lines:
            self.__preprocess_result = self.__calculate_line_bounds
        else:
            self.__preprocess_result = lambda *a: None

    def search(self, paths: List[os.PathLike], recursive: bool = False) -> List[FileMatch]:
        '''Perform search over file located at the specified path'''
        for path in paths:
            try:
                file = open(path)
            except IsADirectoryError as error:
                # Handle directories
                if not recursive:
                    raise error from None
                try:
                    filenames = os.listdir(path)
                    self.search(
                        (pathlib.Path(path) / filename for filename in filenames),
                        recursive=recursive
                    )
                except OSError as error:
                    print(f'{Fore.RED}{Style.BRIGHT}warning:', error, file=sys.stderr)
                except Exception as error:
                    raise error from None
            except OSError as error:
                print(f'evre: {path}: {error.strerror}', file=sys.stderr)
            else:
                # Handle regular files
                self.__process_file(file)
        return self.results

    @staticmethod
    def default_match_handler(_content: str, _begin: int, _end: int, _result: FileMatch) -> bool:
        '''Default match handler accepts every result'''
        return True

    def __calculate_line_bounds(self, result: FileMatch, content: str, match: re.Match):
        # Find full line boundaries
        newline_start = content.rfind('\n', 0, match.span()[0]) + 1
        newline_end = content.find('\n', match.span()[1])
        result.line = content[newline_start:newline_end]
        result.line_offset = newline_start

    def __process_file(self, file: IO):
        try:
            content: str = file.read()
        except UnicodeDecodeError:
            # Likely tried to open a binary file for text output
            return
        matches = self.pattern.finditer(content)
        if self.limit > 0:
            matches = limited(matches, self.limit)
        for match in matches:
            result = FileMatch(file.name, match)
            self.__preprocess_result(result, content, match)
            if self.count_lineno:
                result.lineno = content.count(os.linesep, 0, match.start(0)) + 1
            if self.match_handler(content, *match.span(), result):
                self.results.append(result)
