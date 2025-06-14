#!/usr/bin/env python3

"""Example script.

Example script to search for redundant 'evre::' usages within the 'evre'
namespace using the evrewhere library.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import pathlib
from itertools import islice

from evrewhere import FileMatch, PatternFinder, PatternFinderConfig
from evrewhere.colors import Fore, Style
from evrewhere.printers import MatchPrinter

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    return parser.parse_args(argv)


def find_namespace_used_inside_itself() -> None:
    """Search for redundant '<namespace>::' usages within its own namespace."""
    args = parse_arguments()
    finder = PatternFinder(
        r"\n?(?:namespace (\w+)).*?{.*?(\1::\w+)",
        config=PatternFinderConfig(
            limit=0,
            line_numbers=True,
            case_insensitive=False,
            dot_all=True,
            full_lines=True,
        ),
    )
    columns = []
    max_prefix_width = 0

    def handle_false_positives(
        content: str,
        begin: int,
        end: int,
        result: FileMatch,
    ) -> bool:
        namespace_level = 0
        begin = content.find("{", begin, end)
        for c in islice(content, begin, end):
            if c == "{":
                namespace_level += 1
            elif c == "}":
                namespace_level -= 1
            if not namespace_level:
                return False
        begin = (
            content.rfind("\n", result.match.start(0), result.match.start(2) + 1) + 1
        )
        last_line = content[begin : result.match.start(2)].strip()
        if last_line.lstrip().startswith("//") or last_line.count('"') % 2 != 0:
            return False
        result.lineno += content.count(
            os.linesep,
            result.match.start(0),
            result.match.start(1),
        )
        nonlocal columns, max_prefix_width
        column = result.match.start(2) - begin + 1 + 4  # skip past evre::
        max_prefix_width = max(
            max_prefix_width,
            len(f"{result.path}:{result.lineno}:{column}"),
        )
        columns.append(column)
        return True

    finder.match_handler = handle_false_positives
    logger.info("Searching for redundant evre:: usages within evre namespace")
    use_recursive = any(path.is_dir() for path in args.paths)
    for result, column in zip(
        finder.search(args.paths, recursive=use_recursive),
        columns,
    ):
        logger.info(
            "%-*s %s",
            max_prefix_width,
            f"{result.path}:{result.lineno}:{column}",
            result.match.group(1),
        )
    printer = MatchPrinter(
        None,
        finder.pattern.groups,
        with_filename=True,
        with_lineno=True,
        full_lines=True,
    )
    for result in finder.results:
        printer.log(result)
        logger.info("%s<-- %sunnecessary namespace", Fore.YELLOW, Style.BRIGHT)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        find_namespace_used_inside_itself()
