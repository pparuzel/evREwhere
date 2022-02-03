'''File match module'''

import re
import pathlib
from colorama import Fore, Style

class FileMatch:
    '''Stores regex match information'''
    def __init__(self, path: pathlib.Path, match: re.Match):
        self.path: pathlib.Path = path
        self.match: re.Match = match
        self.lineno: int = 0
        self.line: str = None
        self.line_offset: int = None

    def __str__(self) -> str:
        return (
            f'{Fore.MAGENTA}{self.path}{Fore.BLUE}:{Fore.GREEN}'
            f'{self.lineno or str()}{Fore.BLUE}:{Style.RESET_ALL} {self.match}'
        )

    def __repr__(self) -> str:
        return f'FileMatch("{self.path}", {repr(self.match)})'
