"""Pattern Finder module."""

from __future__ import annotations

import io
import logging
import os
import pathlib
import re
import sys
from typing import IO, TYPE_CHECKING, Any, Callable, NamedTuple

from evrewhere import FileMatch
from evrewhere.colors import Fore, Style

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


DIR_RECURSIVE_SEARCH_REQUIRED_MSG = (
    "Path {} is a directory, but recursive search is not enabled."
)

logger = logging.getLogger(__name__)


def create_pattern(
    pattern_string: str,
    *,
    case_insensitive: re.RegexFlag | None = None,
    dot_all: re.RegexFlag | None = None,
) -> re.Pattern:
    """Convert a pattern string into regex Pattern object."""
    flags = re.MULTILINE
    flags |= dot_all or 0
    flags |= case_insensitive or 0
    return re.compile(pattern_string, flags)


def limited(seq: Iterable, limit: int) -> Generator[Any, Any, None]:
    """Generate a limited number of results."""
    for i, value in enumerate(seq):
        if i >= limit:
            break
        yield value


class PatternFinderConfig(NamedTuple):
    """Configuration options for PatternFinder.

    Attributes:
        limit (int): Maximum number of matches to find.
        line_numbers (bool): Whether to include line numbers in results.
        case_insensitive (bool): Whether the search is case-insensitive.
        dot_all (bool): Whether '.' matches newline characters.
        full_lines (bool): Whether to match and return full lines.
    """

    limit: int = 0
    line_numbers: bool = False
    case_insensitive: bool = False
    dot_all: bool = False
    full_lines: bool = False


class PatternFinder:
    """File and directory search engine based on supplied regex pattern.

    This class allows searching for patterns in files and directories, handling
    both text and binary files. It supports various configurations such as
    case insensitivity, dot-all mode, and line number counting.

    Args:
        pattern (re.Pattern | str): The regex pattern to search for.
            Can be a compiled pattern or a string.
        config (PatternFinderConfig, optional): Configuration for the finder.

    Attributes:
        pattern (re.Pattern): Compiled regex pattern to search for.
        limit (int): Maximum number of matches to find.
        results (list[FileMatch]): List of found matches.
        count_lineno (bool): Whether to count line numbers in results.
        match_handler (Callable): Function to handle matches found.
    """

    def __init__(
        self,
        pattern: re.Pattern | str,
        config: PatternFinderConfig | None = None,
    ) -> None:
        if config is None:
            config = PatternFinderConfig()
        self.pattern: re.Pattern = (
            create_pattern(
                pattern,
                case_insensitive=re.IGNORECASE if config.case_insensitive else None,
                dot_all=re.DOTALL if config.dot_all else None,
            )
            if isinstance(pattern, str)
            else pattern
        )
        self.limit: int = config.limit
        self.results: list[FileMatch] = []
        self.count_lineno: bool = config.line_numbers
        self.match_handler: Callable[[str, int, int, FileMatch], bool] = (
            PatternFinder.default_match_handler
        )
        # Assign the appropriate preprocessing method based on full_lines flag.
        if config.full_lines:
            self.__preprocess_result = self.__calculate_line_bounds
        else:

            def noop_preprocess(
                _result: FileMatch,
                _content: str,
                _match: re.Match,
            ) -> None:
                pass

            self.__preprocess_result = noop_preprocess

    def search(
        self,
        paths: Iterable[os.PathLike | io.TextIOWrapper],
        *,
        recursive: bool = False,
    ) -> list[FileMatch]:
        """Perform search over file located at the specified path."""
        for path_or_stdin in paths:
            if isinstance(path_or_stdin, io.TextIOWrapper):
                self.__process_file(sys.stdin)
                continue
            path = pathlib.Path(path_or_stdin)
            if path.is_dir():
                if not recursive:
                    raise ValueError(DIR_RECURSIVE_SEARCH_REQUIRED_MSG.format(path))
                try:
                    entries = path.iterdir()
                    self.search(
                        entries,
                        recursive=recursive,
                    )
                except OSError as error:
                    logger.warning("%s%s%s", Fore.RED, Style.BRIGHT, error)
                continue
            if path.is_file():
                try:
                    with path.open() as file:
                        self.__process_file(file)
                except OSError as error:
                    logger.exception(
                        "%s%s%s: %s",
                        Fore.RED,
                        Style.BRIGHT,
                        path,
                        error.strerror,
                    )
                continue
            logger.warning(
                "%s%s%s is not a regular file and was skipped.",
                Fore.YELLOW,
                Style.BRIGHT,
                path,
            )
        return self.results

    @staticmethod
    def default_match_handler(
        _content: str,
        _begin: int,
        _end: int,
        _result: FileMatch,
    ) -> bool:
        """Default match handler accepts every result."""
        return True

    def __calculate_line_bounds(
        self,
        result: FileMatch,
        content: str,
        match: re.Match,
    ) -> None:
        # Find full line boundaries
        newline_start = content.rfind("\n", 0, match.span()[0]) + 1
        newline_end = content.find("\n", match.span()[1])
        result.line = content[newline_start:newline_end]
        result.line_offset = newline_start

    def __process_file(self, file: IO) -> None:
        try:
            content: str = file.read()
        except UnicodeDecodeError:
            # Likely tried to open a binary file for text output.
            return
        matches = self.pattern.finditer(content)
        if self.limit > 0:
            matches = limited(matches, self.limit)
        for match in matches:
            result = FileMatch(pathlib.Path(file.name), match)
            self.__preprocess_result(result, content, match)
            if self.count_lineno:
                result.lineno = content.count(os.linesep, 0, match.start(0)) + 1
            begin, end = match.span()
            if self.match_handler(content, begin, end, result):
                self.results.append(result)
