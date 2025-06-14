"""File match module."""

import pathlib
import re

from evrewhere.colors import Fore, Style


class FileMatch:
    """Stores regex match information."""

    def __init__(self, path: pathlib.Path, match: re.Match) -> None:
        """Initializes the object with the given file path and regex match.

        Args:
            path (pathlib.Path): The path to the file being processed.
            match (re.Match): The regular expression match object.

        Attributes:
            path (pathlib.Path): The path to the file.
            match (re.Match): The regular expression match object.
            lineno (int): The line number in the file.
            line (str): The content of the matched line.
            line_offset (int): The offset of the match within the line.
        """
        self.path: pathlib.Path = path
        self.match: re.Match = match
        self.lineno: int = 0
        self.line: str = ""
        self.line_offset: int = 0

    def __str__(self) -> str:
        """Generate a string representation of the FileMatch object.

        Return a color-formatted string representation of the object, including
        the file path, line number (if available), and the matched text. The
        output uses color codes for enhanced readability in supported terminals.

        """
        return (
            f"{Fore.MAGENTA}{self.path}{Fore.BLUE}:{Fore.GREEN}"
            f"{self.lineno or ''}{Fore.BLUE}:{Style.RESET_ALL} {self.match}"
        )

    def __repr__(self) -> str:
        """Return a string representation of the FileMatch object.

        The returned string includes the file path and the match attribute,
        formatted for easy debugging and logging.
        """
        return f'FileMatch("{self.path}", {self.match!r})'
