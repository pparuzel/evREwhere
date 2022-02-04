#!/usr/bin/env python3
'''Example'''

import os
import sys
import pathlib
import argparse

# Workaround to not require installing the module
sys.path.append(str(pathlib.Path(os.path.dirname(__file__)).parent))

from evrewhere import PatternFinder, FileMatch
from evrewhere.colors import Fore, Style


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+', type=pathlib.Path)
    return parser.parse_args()


def find_incorrect_cpp20_class_constructors():
    args = parse_arguments()
    finder = PatternFinder(
        r'template[^\n]+\n[^\n]*class\s+(\w\w+)\b.*?(\1<[^\n]*?>)\(',
        limit=1,
        line_numbers=True,
        dot_all=True,
    )
    def handle_false_positives(content: str, begin: int, end: int, result: FileMatch):
        # If the match contains '};' this may be a class ending
        # so the regex may have found a false-positive
        result.lineno += content.count(os.linesep, result.match.start(0), result.match.start(2))
        prefix = f'{Fore.YELLOW}MAYBE' if content.count('};', begin, end) > 0 else f'{Fore.GREEN}FOUND'
        class_name = result.match.group(1)
        print(f'{Style.BRIGHT}{prefix}{Style.RESET_ALL} {result.path}:{result.lineno} class={Fore.RED}{class_name}')

    finder.match_handler = handle_false_positives
    finder.search(args.paths, recursive=any(path.is_dir() for path in args.paths))


if __name__ == '__main__':
    try:
        find_incorrect_cpp20_class_constructors()
    except KeyboardInterrupt:
        pass
