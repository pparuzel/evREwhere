#!/usr/bin/env python3

'''evREwhere is a pattern searcher like grep but enables extended capabilities

evREwhere can be used as a module or a separate utility program

Examples needed here...
'''

from typing import Callable, Union, Iterable, List

import os
import re
import sys
import pathlib
import argparse
from colorama import init as init_colorama, Fore, Style


__all__ = ['PatternFinder', 'FileMatch']


init_colorama(autoreset=True)


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


def parse_arguments():
    '''Parse program arguments'''
    def postparse(args: argparse.Namespace):
        '''Post-parse program arguments'''
        if args.path.is_dir() and not args.recursive:
            raise ValueError('Supplied path is a directory but the search is not recursive')
        return args

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', type=pathlib.Path,
        help='path to a directory (-r required) or file'
    )
    parser.add_argument(
        'pattern',
        help='pattern used in search'
    )
    parser.add_argument(
        '-r', action='store_true', dest='recursive', default=False,
        help='recursive search'
    )
    parser.add_argument(
        '-m', dest='limit', type=int, default=0,
        help='maximum matches (default: no limit)'
    )
    parser.add_argument(
        '-n', '--lineno', dest='display_lineno', action='store_true',
        help='whether to display line numbers (may affect performance)'
    )
    parser.add_argument(
        '-i', '--ignore-case', dest='case_insensitive', action='store_true',
        help='case insensitive search'
    )
    parser.add_argument(
        '-a', '--dot-all', dest='dot_all', action='store_true',
        help='dot (.) includes newline characters'
    )
    parser.add_argument(
        '-f', '--format', dest='template', default='{0}',
        help='display format, {0} means group(0) (default: {0})'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', dest='verbose',
        help='outputs regex Match object instead of raw text'
    )
    args = parser.parse_args()
    try:
        return postparse(args)
    except ValueError as error:
        parser.error(error)


class FileMatch:
    '''Store file path, regex Match object and optionally the line number'''
    def __init__(self, path: pathlib.Path, match: re.Match):
        self.path: pathlib.Path = path
        self.match: re.Match = match
        self.lineno: int = 0

    def __str__(self):
        return (
            f'{Fore.MAGENTA}{self.path.name}{Fore.BLUE}:{Fore.GREEN}'
            f'{self.lineno or str()}{Fore.BLUE}:{Style.RESET_ALL} {self.match}'
        )

    def __repr__(self):
        return f'FileMatch("{self.path.name}", {repr(self.match)})'


class PatternFinder:
    '''File and directory search engine based on supplied regex pattern'''
    def __init__(
        self,
        pattern: Union[re.Pattern, str], *,  # pylint: disable=E1136
        limit: int = 0,
        line_numbers: bool = False,
        case_insensitive: bool = False,
        dot_all: bool = False
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
        self.results: list[FileMatch] = []
        self.with_lineno: bool = line_numbers
        self.match_handler: Callable[[str, int, int, FileMatch], bool] = \
            PatternFinder.default_match_handler

    def search(self, path: os.PathLike, recursive: bool = False) -> List[FileMatch]:
        '''Perform search over file located at the specified path'''
        path = pathlib.Path(path)
        if path.is_file():
            self.__process_file(path)
            return self.results
        if not recursive:
            error_hint = '. Consider a recursive search' if path.is_dir() else ''
            raise OSError('Supplied path is not a regular file' + error_hint)
        for file in (pathlib.Path(path / file) for file in os.listdir(path)):
            self.__search_recursive(file)
        return self.results

    @staticmethod
    def default_match_handler(_content: str, _begin: int, _end: int, _result: FileMatch) -> bool:
        '''Default match handler accepts every result'''
        return True

    def __process_file(self, path: pathlib.Path):
        try:
            content = open(path).read()
        except UnicodeDecodeError:
            # Likely tried to open a binary file for text output
            return
        matches = self.pattern.finditer(content)
        if self.limit > 0:
            matches = limited(matches, self.limit)
        for match in matches:
            result = FileMatch(path, match)
            if self.with_lineno:
                result.lineno = content.count(os.linesep, 0, match.start(0)) + 1
            if self.match_handler(content, *match.span(), result):
                self.results.append(result)

    def __search_recursive(self, path: pathlib.Path):
        if path.is_file():
            self.__process_file(path)
            return
        if path.is_dir():
            try:
                for file in os.listdir(path):
                    self.__search_recursive(pathlib.Path(path / file))
            except OSError as error:
                print(f'{Fore.RED}{Style.BRIGHT}warning:', error, file=sys.stderr)
        # Else, skip unsupported file-like objects (like fifos)


def main():
    '''Run program as a utility with argument parsing'''
    args = parse_arguments()
    finder = PatternFinder(
        args.pattern,
        limit=args.limit,
        line_numbers=args.display_lineno,
        case_insensitive=args.case_insensitive,
        dot_all=args.dot_all
    )
    for result in finder.search(args.path, recursive=args.recursive):
        if args.verbose:
            print(result)
        else:
            lineno_part = f'{Fore.GREEN}{result.lineno}{Fore.CYAN}:' if args.display_lineno else ''
            print(
                (f'{Fore.MAGENTA}{result.path}{Fore.CYAN}:' if args.recursive else '') +
                str(lineno_part) +
                f'{Style.RESET_ALL}' +
                args.template.format(result.match.group(0), *result.match.groups())
            )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
