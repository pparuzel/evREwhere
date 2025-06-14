"""Printers module."""

from __future__ import annotations

import logging
from itertools import cycle
from typing import TYPE_CHECKING

from evrewhere.colors import COLORS, Fore, Style

if TYPE_CHECKING:
    from evrewhere.file_match import FileMatch


logger = logging.getLogger(__name__)


class VerbosePrinter:
    """Regular printer that shows the result object."""

    def log(self, result: FileMatch) -> None:
        """Logs the result object.

        Args:
            result (FileMatch): The result object to log.
        """
        logger.info(result)


class FileInfoPrefixFormat:
    """Provides colored formats for file info prefixes."""

    def __init__(
        self,
        *,
        with_filename: bool = False,
        with_lineno: bool = False,
    ) -> None:
        """Initializes the printer configuration.

        Args:
            with_filename (bool, optional): If True, includes the filename in
            the output format. Defaults to False.
            with_lineno (bool, optional): If True, includes the line number in
            the output format. Defaults to False.

        Attributes:
            filename_format (str): Format string for displaying the filename,
                colored if enabled.
            linenumber_format (str): Format string for displaying the line
                number, colored if enabled.

        """
        self.filename_format: str = (
            f"{Fore.MAGENTA}" + "{path}" + f"{Fore.CYAN}:" if with_filename else ""
        )
        self.linenumber_format: str = (
            f"{Fore.GREEN}" + "{lineno}" + f"{Fore.CYAN}:" if with_lineno else ""
        )

    def prefixes(self, path: str, lineno: int) -> str:
        """Generates and returns a formatted prefix string for a file match.

        Args:
            path (str): The file path to include in the prefix.
            lineno (int): The line number to include in the prefix.

        Returns:
            str: A formatted string containing the file path, line number, and
                a style reset sequence.

        """
        # Returns prefixes for the FileMatch
        return (
            # File path part
            self.filename_format.format(path=path)
            +
            # Line number part
            self.linenumber_format.format(lineno=lineno)
            +
            # Drop all styles
            Style.RESET_ALL
        )


class FileInfoPrefixPrinter(FileInfoPrefixFormat):
    """Prints colored filename and line number prefixes."""

    def log(self, path: str, lineno: int, extra: str = "") -> None:
        """Logs the colored filename and line number prefixes.

        Args:
            path (str): The file path to include in the prefix.
            lineno (int): The line number to include in the prefix.
            extra (str, optional): Additional information to log after the
                prefixes. Defaults to an empty string.

        """
        logger.info("%s%s", self.prefixes(path, lineno), extra)


class MatchPrinter(FileInfoPrefixFormat):
    """Sophisticated printer that handles prefixes and templates.

    Args:
        template (str | None): The template string used for formatting.
            If None, a colored match processor is used.
        group_count (int): The number of groups to process in the match.
        with_filename (bool, optional): Whether to include the filename in
            the output. Defaults to False.
        with_lineno (bool, optional): Whether to include the line number in
            the output. Defaults to False.
        full_lines (bool, optional): Whether to print full lines in the
            output. Defaults to False.

    Notes:
        If `template` is None, the colored match processor is used.
        Otherwise, the template processor is used.

    """

    def __init__(
        self,
        template: str | None,
        group_count: int,
        *,
        with_filename: bool = False,
        with_lineno: bool = False,
        full_lines: bool = False,
    ) -> None:
        super().__init__(with_filename=with_filename, with_lineno=with_lineno)
        self.template = template or "{0}"
        self.group_count = group_count
        self.full_lines = full_lines
        if template is None:
            self.process_match = self.__process_match_colored
        else:
            self.process_match = self.__process_match_template

    def __process_match_template(self, result: FileMatch) -> str:
        return self.template.format(
            result.match.group(0),
            *result.match.groups(),
            **COLORS,
        )

    def __process_match_colored(self, result: FileMatch) -> str:
        color = cycle(COLORS.values())
        output = ""
        last_end = 0
        if self.full_lines:
            fullmatch = result.line
            offset = result.line_offset
        else:
            fullmatch = result.match.group(0)
            offset = result.match.span()[0]
        # Must be defined when captures are searched but not found.
        end = 0
        for i in range(self.group_count):
            if not result.match.group(i + 1):
                continue
            # Wrap captures with colors.
            start = result.match.start(i + 1) - offset
            end = result.match.end(i + 1) - offset
            output += fullmatch[last_end:start] + Style.BRIGHT + next(color)
            output += fullmatch[start:end] + Style.RESET_ALL
            last_end = end
        output += fullmatch[end:] + Style.RESET_ALL
        return output

    def log(self, result: FileMatch) -> None:
        """Logs the formatted match result.

        Args:
            result (FileMatch): The result object containing match information.

        """
        logger.info(
            "%s%s",
            self.prefixes(str(result.path), result.lineno),
            self.process_match(result),
        )
