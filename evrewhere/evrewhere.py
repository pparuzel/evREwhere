#!/usr/bin/env python3

'''evREwhere is a pattern searcher like grep but enables extended capabilities

evREwhere can be used as a module or a separate utility program

Examples needed here...
'''

from typing import Callable, Union, Iterable, List, IO

import os
import re
import sys
import pathlib
import argparse
import collections
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
        if args.count_only:
            if args.with_lineno:
                raise ValueError('-n and -c are mutually exclusive')
        if args.with_filename is None:
            args.with_filename = args.recursive or len(args.paths) > 1
        elif args.verbose and not args.with_filename:
            raise ValueError('--verbose does not support -h/--no-filename')
        return args

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--help', action='help', default=argparse.SUPPRESS,
        help='show this help message and exit'
    )
    parser.add_argument(
        'pattern',
        help='pattern used in search'
    )
    parser.add_argument(
        'paths', nargs='+', type=pathlib.Path,
        help='path to a directory (-r required) or file'
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
        '-n', '--lineno', dest='with_lineno', action='store_true',
        help='whether to display line numbers (may affect performance)'
    )
    parser.add_argument(
        '-f', '--format', dest='template', default='{0}',
        help='display format, {0} means group(0) (default: {0})'
    )
    parser.add_argument(
        '-H', '--with-filename', dest='with_filename', action='store_true', default=None,
        help='print file name with output lines'
    )
    parser.add_argument(
        '-h', '--no-filename', dest='with_filename', action='store_false', default=None,
        help='suppress the file name prefix on output'
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
        '-q', '--quiet', '--silent', dest='quiet', action='store_true',
        help='suppress all normal output'
    )
    parser.add_argument(
        '-c', '--count', dest='count_only', action='store_true',
        help='print only a (positive) number of matches per file'
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
            f'{Fore.MAGENTA}{self.path}{Fore.BLUE}:{Fore.GREEN}'
            f'{self.lineno or str()}{Fore.BLUE}:{Style.RESET_ALL} {self.match}'
        )

    def __repr__(self):
        return f'FileMatch("{self.path}", {repr(self.match)})'


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
        self.results: List[FileMatch] = []
        self.count_lineno: bool = line_numbers
        self.match_handler: Callable[[str, int, int, FileMatch], bool] = \
            PatternFinder.default_match_handler

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

    def __process_file(self, file: IO):
        try:
            content = file.read()
        except UnicodeDecodeError:
            # Likely tried to open a binary file for text output
            return
        matches = self.pattern.finditer(content)
        if self.limit > 0:
            matches = limited(matches, self.limit)
        for match in matches:
            result = FileMatch(file.name, match)
            if self.count_lineno:
                result.lineno = content.count(os.linesep, 0, match.start(0)) + 1
            if self.match_handler(content, *match.span(), result):
                self.results.append(result)


def main():
    '''Run program as a utility with argument parsing'''
    args = parse_arguments()
    finder = PatternFinder(
        args.pattern,
        limit=args.limit,
        line_numbers=args.with_lineno,
        case_insensitive=args.case_insensitive,
        dot_all=args.dot_all
    )
    found = finder.search(args.paths, recursive=args.recursive)
    exit_code = int(not found)
    if args.count_only:
        counts = collections.Counter(result.path for result in found)
        for path in counts:
            print(
                # File path part
                (f'{Fore.MAGENTA}{path}{Fore.CYAN}:' if args.with_filename else '') +
                # Drop current style
                f'{Style.RESET_ALL}'
                # Display the number of matches
                f'{counts[path]}'
            )
        return exit_code
    for result in found:
        if args.quiet:
            continue
        if args.verbose:
            print(result)
        else:
            print(
                # File path part
                (f'{Fore.MAGENTA}{result.path}{Fore.CYAN}:' if args.with_filename else '') +
                # Line number part
                (f'{Fore.GREEN}{result.lineno}{Fore.CYAN}:' if args.with_lineno else '') +
                # Drop current style
                f'{Style.RESET_ALL}' +
                # Match
                args.template.format(result.match.group(0), *result.match.groups())
            )
    return exit_code


if __name__ == '__main__':
    EXIT_CODE = 1
    try:
        EXIT_CODE = main()
    except KeyboardInterrupt:
        EXIT_CODE = 130
    except OSError as error:
        print(f'evre: {error.filename}: {error.strerror}')
        EXIT_CODE = 2
    sys.exit(EXIT_CODE)
