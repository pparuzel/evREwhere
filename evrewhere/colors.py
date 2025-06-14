"""Colors module."""

import os

if os.getenv("EVREDONTUSECOLOR", "") == "1":

    def init_colorama(*args, **kwargs) -> None:
        """No colorama initializer."""

    class NoColoramaWrapper:
        def __getattr__(self, _attr: str) -> str:
            """Return empty string for any attribute."""
            return ""

    Fore = Style = NoColoramaWrapper()
else:
    from colorama import Fore, Style
    from colorama import init as init_colorama


__all__ = ["COLORS", "Fore", "Style", "init_colorama"]


init_colorama(autoreset=True)


COLORS = {
    "RED": Fore.RED,
    "GREEN": Fore.GREEN,
    "YELLOW": Fore.YELLOW,
    "BLUE": Fore.BLUE,
    "MAGENTA": Fore.MAGENTA,
    "CYAN": Fore.CYAN,
    "None": Fore.RESET,
}
