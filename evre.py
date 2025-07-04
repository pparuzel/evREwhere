#!/usr/bin/env python3

"""evREwhere is a pattern searcher like grep but enables extended capabilities.

evREwhere can be used as a module or a separate utility program

"""

from __future__ import annotations

import argparse
import collections
import logging
import pathlib
import sys
from typing import NoReturn

from evrewhere import PatternFinder, PatternFinderConfig
from evrewhere.printers import FileInfoPrefixPrinter, MatchPrinter, VerbosePrinter

COUNT_LINENO_MUT_EXCL = "-n and -c are mutually exclusive"
COUNT_FULL_LINES_MUT_EXCL = "--full-lines and --count are mutually exclusive"
FULL_LINES_FORMAT_MUT_EXCL = "--full-lines and --format are mutually exclusive"
VERBOSE_NO_FILENAME_EXCL = "--verbose does not support -h/--no-filename"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("evrewhere")


def postparse(args: argparse.Namespace) -> argparse.Namespace:
    """Validate parsed arguments.

    Post-processes parsed command-line arguments to enforce mutual
    exclusions, set defaults, and validate input.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        argparse.Namespace: The updated and validated arguments namespace.

    Raises:
        ValueError: If required arguments are missing, or if mutually exclusive
            options are used together.

    """
    # Post-parse program arguments
    if not sys.stdin.isatty():
        args.paths.append(sys.stdin)
    elif not args.paths:
        msg = "No paths provided, please specify a file or directory."
        raise ValueError(msg)
    if args.count_only:
        if args.with_lineno:
            msg = COUNT_LINENO_MUT_EXCL
            raise ValueError(msg)
        if args.full_lines:
            raise ValueError(COUNT_FULL_LINES_MUT_EXCL)
    if args.full_lines and args.template is not None:
        raise ValueError(FULL_LINES_FORMAT_MUT_EXCL)
    if args.with_filename is None:
        args.with_filename = args.recursive or len(args.paths) > 1
    elif args.verbose and not args.with_filename:
        raise ValueError(VERBOSE_NO_FILENAME_EXCL)
    return args


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the evREwhere utility.

    Returns:
        argparse.Namespace: Parsed arguments with defaults applied

    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="show this help message and exit",
    )
    parser.add_argument(
        "pattern",
        help="pattern used in search",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=pathlib.Path,
        help="path to a directory (-r required) or file",
    )
    parser.add_argument(
        "-r",
        action="store_true",
        dest="recursive",
        default=False,
        help="recursive search",
    )
    parser.add_argument(
        "-m",
        dest="limit",
        type=int,
        default=0,
        help="maximum matches (default: no limit)",
    )
    parser.add_argument(
        "-n",
        "--lineno",
        dest="with_lineno",
        action="store_true",
        help="whether to display line numbers (may affect performance)",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="template",
        default=None,
        help="display format, {0} means group(0) (default: {0})",
    )
    parser.add_argument(
        "-H",
        "--with-filename",
        dest="with_filename",
        action="store_true",
        default=None,
        help="print file name with output lines",
    )
    parser.add_argument(
        "-h",
        "--no-filename",
        dest="with_filename",
        action="store_false",
        default=None,
        help="suppress the file name prefix on output",
    )
    parser.add_argument(
        "-g",
        "--full-lines",
        dest="full_lines",
        action="store_true",
        help="print full lines like grep (may affect performance)",
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        dest="case_insensitive",
        action="store_true",
        help="case insensitive search",
    )
    parser.add_argument(
        "-a",
        "--dot-all",
        dest="dot_all",
        action="store_true",
        help="dot (.) includes newline characters",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        "--silent",
        dest="quiet",
        action="store_true",
        help="suppress all normal output",
    )
    parser.add_argument(
        "-c",
        "--count",
        dest="count_only",
        action="store_true",
        help="print only a (positive) number of matches per file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="outputs regex Match object instead of raw text",
    )
    args = parser.parse_args(argv)
    try:
        return postparse(args)
    except ValueError as error:
        parser.error(str(error))


def parse_and_run(argv: list[str] | None = None) -> int:
    """Run the evREwhere utility with argument parsing.

    Returns:
        int: 0 if a match was found, 1 if none were found.
    """
    args = parse_arguments(argv)
    finder = PatternFinder(
        args.pattern,
        PatternFinderConfig(
            limit=args.limit,
            line_numbers=args.with_lineno,
            case_insensitive=args.case_insensitive,
            dot_all=args.dot_all,
            full_lines=args.full_lines,
        ),
    )
    found = finder.search(args.paths, recursive=args.recursive)
    exit_code = int(not found)
    if args.count_only:
        prefix_printer = FileInfoPrefixPrinter(with_filename=args.with_filename)
        counts = collections.Counter(result.path for result in found)
        for path in counts:
            prefix_printer.log(str(path), 0, str(counts[path]))
        return exit_code
    if args.quiet:
        return exit_code
    if args.verbose:
        printer = VerbosePrinter()
    else:
        printer = MatchPrinter(
            args.template,
            finder.pattern.groups,
            with_filename=args.with_filename,
            with_lineno=args.with_lineno,
            full_lines=args.full_lines,
        )
    # Show results
    for result in found:
        printer.log(result)
    return exit_code


def main() -> NoReturn:
    """Main function to run the evREwhere utility."""
    exit_code = 255
    try:
        exit_code = parse_and_run()
    except KeyboardInterrupt:
        exit_code = 130
    except OSError as error:
        logger.exception("evre: %s: %s", error.filename, error.strerror)
        exit_code = 2
    except Exception:
        logger.exception("evre: unexpected error")
        exit_code = 1
    except SystemExit:
        pass
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
