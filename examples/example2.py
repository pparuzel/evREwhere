#!/usr/bin/env python3

import os
import sys
import pathlib
import argparse
from itertools import islice

# Workaround to not require installing the module
sys.path.append(str(pathlib.Path(os.path.dirname(__file__)).parent))

from evrewhere import PatternFinder, FileMatch
from evrewhere.colors import Fore, Style
from evrewhere.printers import MatchPrinter


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+', type=pathlib.Path)
    return parser.parse_args()


def find_namespace_used_inside_itself():
    args = parse_arguments()
    finder = PatternFinder(
        r'\n?(namespace evre).*?{.*?(evre::\w+)',
        limit=0,
        line_numbers=True,
        case_insensitive=False,
        dot_all=True,
        full_lines=True,
    )
    columns = []
    max_prefix_width = 0
    def handle_false_positives(content: str, begin: int, end: int, result: FileMatch):
        namespace_level = 0
        begin = content.find('{', begin, end)
        for c in islice(content, begin, end):
            if c == '{':
                namespace_level += 1
            elif c == '}':
                namespace_level -= 1
            if not namespace_level:
                return False
        begin = content.rfind('\n', result.match.start(0), result.match.start(2) + 1) + 1
        last_line = content[begin:result.match.start(2)].strip()
        if last_line.lstrip().startswith('//') or last_line.count('"') % 2 != 0:
            return False
        result.lineno += content.count(os.linesep, result.match.start(0), result.match.start(1))
        nonlocal columns, max_prefix_width
        column = result.match.start(2) - begin + 1 + 4  # skip past evre::
        max_prefix_width = max(max_prefix_width, len(f'{result.path}:{result.lineno}:{column}'))
        columns.append(column)
        return True

    finder.match_handler = handle_false_positives
    print('Searching for redundand evre:: usages within evre namespace')
    for result, column in zip(finder.search(args.paths, recursive=any(path.is_dir() for path in args.paths)), columns):
        print(
            '{0:{2}} {1}'.format(
                f'{result.path}:{result.lineno}:{column}', result.match.group(1), max_prefix_width
            )
        )
    printer = MatchPrinter(None, finder.pattern.groups, with_filename=True, with_lineno=True, full_lines=True)
    for result in finder.results:
        printer.print(result, f'{Fore.YELLOW}<-- {Style.BRIGHT}unnecessary namespace')


if __name__ == '__main__':
    try:
        find_namespace_used_inside_itself()
    except KeyboardInterrupt:
        pass
