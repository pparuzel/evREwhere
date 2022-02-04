'''Colors module'''

import os

if os.getenv('EVREDONTUSECOLOR', '') == '1':
    def init_colorama(*_a, **_kw):
        '''No colorama initializer'''

    class NoColoramaWrapper:
        '''No colorama wrapper'''
        def __getattr__(self, _attr):
            return ''

    Fore = Style = NoColoramaWrapper()
else:
    from colorama import init as init_colorama, Fore, Style


__all__ = ['COLORS', 'Fore', 'Style', 'init_colorama']


init_colorama(autoreset=True)


COLORS = {
    'RED': Fore.RED,
    'GREEN': Fore.GREEN,
    'YELLOW': Fore.YELLOW,
    'BLUE': Fore.BLUE,
    'MAGENTA': Fore.MAGENTA,
    'CYAN': Fore.CYAN,
    'None': Fore.RESET,
}
