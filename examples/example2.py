#!/usr/bin/env python3

import os
import pathlib
import argparse
from itertools import islice
from evrewhere import PatternFinder, FileMatch


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=pathlib.Path)
    return parser.parse_args()


def find_namespace_used_inside_itself():
    args = parse_arguments()
    finder = PatternFinder(
        r'namespace sf.*?{.*?(sf::\w+)',
        limit=0,
        line_numbers=True,
        case_insensitive=False,
        dot_all=True,
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
        begin = content.rfind('\n', result.match.start(0), result.match.start(1) + 1) + 1
        last_line = content[begin:result.match.start(1)].strip()
        if last_line.lstrip().startswith('//') or last_line.count('"') % 2 != 0:
            return False
        result.lineno += content.count(os.linesep, result.match.start(0), result.match.start(1))
        nonlocal columns, max_prefix_width
        column = result.match.start(1) - begin + 1 + 4  # skip past sf::
        max_prefix_width = max(max_prefix_width, len(f'{result.path}:{result.lineno}:{column}'))
        columns.append(column)
        return True

    finder.match_handler = handle_false_positives
    print('Searching for redundand sf:: usages within sf namespace')
    for result, column in zip(finder.search(args.path, recursive=args.path.is_dir()), columns):
        print(
            '{0:{2}} {1}'.format(
                f'{result.path}:{result.lineno}:{column}', result.match.group(1), max_prefix_width
            )
        )


if __name__ == '__main__':
    try:
        find_namespace_used_inside_itself()
    except KeyboardInterrupt:
        pass
