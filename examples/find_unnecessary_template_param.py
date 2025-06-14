#!/usr/bin/env python3
"""Example."""

import argparse
import contextlib
import logging
import os
import pathlib

from evrewhere import FileMatch, PatternFinder, PatternFinderConfig
from evrewhere.colors import Fore, Style

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger()


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    return parser.parse_args()


def find_incorrect_cpp20_class_constructors() -> None:
    """Search for potentially incorrect C++20 class constructors.

    Parses command-line arguments to determine file paths, then uses a regular
    expression to find class constructors that may have redundant template
    parameters. For each match, checks for possible false positives (such as
    class endings) and prints the result with context.

    """
    args = parse_arguments()
    finder = PatternFinder(
        r"template[^\n]+\n[^\n]*class\s+(\w\w+)\b.*?(\1<[^\n]*?>)\(",
        PatternFinderConfig(limit=1, line_numbers=True, dot_all=True),
    )

    def handle_false_positives(
        content: str,
        begin: int,
        end: int,
        result: FileMatch,
    ) -> bool:
        result.lineno += content.count(
            os.linesep,
            result.match.start(0),
            result.match.start(2),
        )
        # If the match contains '};' this may be a class ending.
        # That means the regex may have found a false-positive.
        prefix = (
            f"{Fore.YELLOW}MAYBE"
            if content.count("};", begin, end) > 0
            else f"{Fore.GREEN}FOUND"
        )
        class_name = result.match.group(1)
        logger.info(
            "%s%s%s %s:%d class=%s%s",
            Style.BRIGHT,
            prefix,
            Style.RESET_ALL,
            result.path,
            result.lineno,
            Fore.RED,
            class_name,
        )
        return False

    finder.match_handler = handle_false_positives
    finder.search(args.paths, recursive=any(path.is_dir() for path in args.paths))


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        find_incorrect_cpp20_class_constructors()
