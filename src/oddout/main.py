import contextlib
import sys

import atexit
import functools
import shutil
import textwrap
import threading
import time

from html.parser import HTMLParser
from typing import Any

from colorama import *

from pyoload import *


'''
###############################################################################
######################## modified extract from colorama #######################
###############################################################################
'''


CSI = '\033['
OSC = '\033]'
BEL = '\a'


def code_to_chars(code):
    return CSI + str(code) + 'm'


def set_title(title):
    return OSC + '2;' + title + BEL


def clear_screen(mode=2):
    return CSI + str(mode) + 'J'


def clear_line(mode=2):
    return CSI + str(mode) + 'K'


class AnsiCodes(object):
    def __init__(self):
        # the subclasses declare class attributes which are numbers.
        # Upon instantiation we define instance attributes, which are the same
        # as the class attributes but wrapped with the ANSI escape sequence
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, code_to_chars(value))

    def __call__(self, name="reset"):
        return getattr(self, name.upper())


class AnsiCursor(object):
    def UP(self, n=1):
        return CSI + str(n) + 'A'

    def DOWN(self, n=1):
        return CSI + str(n) + 'B'

    def FORWARD(self, n=1):
        return CSI + str(n) + 'C'

    def BACK(self, n=1):
        return CSI + str(n) + 'D'

    def POS(self, x=1, y=1):
        return CSI + str(y) + ';' + str(x) + 'H'


class AnsiFore(AnsiCodes):
    BLACK           = 30
    RED             = 31
    GREEN           = 32
    YELLOW          = 33
    BLUE            = 34
    MAGENTA         = 35
    CYAN            = 36
    WHITE           = 37
    RESET           = 39

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 90
    LIGHTRED_EX     = 91
    LIGHTGREEN_EX   = 92
    LIGHTYELLOW_EX  = 93
    LIGHTBLUE_EX    = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX    = 96
    LIGHTWHITE_EX   = 97


class AnsiBack(AnsiCodes):
    BLACK           = 40
    RED             = 41
    GREEN           = 42
    YELLOW          = 43
    BLUE            = 44
    MAGENTA         = 45
    CYAN            = 46
    WHITE           = 47
    RESET           = 49

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 100
    LIGHTRED_EX     = 101
    LIGHTGREEN_EX   = 102
    LIGHTYELLOW_EX  = 103
    LIGHTBLUE_EX    = 104
    LIGHTMAGENTA_EX = 105
    LIGHTCYAN_EX    = 106
    LIGHTWHITE_EX   = 107


class AnsiStyle(AnsiCodes):
    BRIGHT    = 1
    DIM       = 2
    NORMAL    = 22
    RESET_ALL = 0


Fore   = AnsiFore()
Back   = AnsiBack()
Style  = AnsiStyle()
Cursor = AnsiCursor()


'''
###############################################################################
################################## extract end ################################
###############################################################################
'''

init()
width, height = shutil.get_terminal_size()


def update_terminal_sizes():
    global width, height
    width, height = shutil.get_terminal_size()


def em(text, border_color="green", text_color="white"):
    f_b = Fore(border_color)
    f_t = Fore(text_color)
    text = textwrap.wrap(text, width - 2)
    mw = max(map(len, text))
    lo = (width - 1 - mw) // 2
    print(f_b + width * '─')
    for ln in text:
        ln = '> ' + ln + ';'
        print(f_t + lo * ' ' + ln)
    print(f_b + width * '─')


def error(e):
    em(
        e.__class__.__name__ + ": " + str(e),
        border_color="red",
        text_color="red"
    )


def ellipsis(le=3, ch='.', s=' '):
    i = 0
    print("   ", end="")
    while True:
        yield
        i += 1
        i %= (le + 1)
        print((i * ch).ljust(le, s), end=Cursor.BACK(3))


@contextlib.contextmanager
def Errors():
    try:
        yield error
    except Exception as e:
        error(e)


class BaseHandle:
    sub_handles = []
    child: Any = None
    name = 'base'

    def __enter__(self):
        pass

    def __leave__(self):
        del self

    def __del__(self):
        atexit.unregister(self.__leave__)
        if hasattr(super(), '__del__'):
            super().__del__()

    def __init__(self, attrs):
        self.attrs = attrs
        self.__enter__()

        atexit.register(self.__leave__)

    def __init_subclass__(cls):
        BaseHandle.sub_handles.append(cls)

    def starttag(self, name, attrs):
        for handle in BaseHandle.sub_handles:
            if handle.name == name:
                sub = handle(attrs)
                self.child = sub
                scope.append(sub)
        else:
            error(f'TagError: tag {name!r} unknown')

    def endtag(self, name):
        if name == self.name:
            for _ in range(len(scope) - scope.index(self)):
                scope.pop()
            self.__leave__()

    def tag(self, name, attrs):
        pass

    def data(self, data):
        print(data.strip())
###############################################################################


class ProgressBar(BaseHandle):
    @annotate
    def register(max: Cast(float), val: Cast(float) = 0, alpha: float = 0.3):
        t1 = time.perf_counter()  # the current time from unknown origin
        last = 0
        speed = 0
        calls = 0
        remaining = 0
        while True:
            with Errors():  # all errors formatted to stdout
                new = yield (last, speed, remaining)
            a, b = alpha, 1 - alpha
            new = a * last + b * new
            last = last / (1 - b ** calls) if calls else last

    name = "progressbar"

    @annotate
    def __enter__(self):
        self.t = time.perf_counter()
        self.lastSpeed = self.calls = self.last = self.lastVal = 0
        self.alpha = float(self.attrs.get(alpha), 0.3)
        self.max = float(self.attrs.get(max), 100)
        self.main_proc_name = self.attrs.get("name", "main")
        self.procs = {
            self.main_proc_name: 0
        }

    def tag(self, name, attrs):
        if name == "progress":
            proc_name = attrs.get("proc", self.main_proc_name)
            try:
                val = attrs["value"]
            except IndexError:
                return error(
                    ValueError('Called progress without specifying value'),
                )
            self.procs[proc_name] = val
        self.update()

    def update(self, char='-'):
        update_terminal_sizes()



    def __exit__(self):
        print(Cursor.DOWN(self.height), end="\r")

###############################################################################


class Ellipsis(BaseHandle):
    name = 'ellipsis'

    def __enter__(self):
        self.len = int(self.attrs.get('len', '3'))
        self.dur = float(self.attrs.get('dur', '0.5'))
        self.stop = False
        self.pause = False

        self.thread = threading.Thread(target=self.inner)
        self.thread.start()

        return self.do_pause

    def __leave__(self, e=None):
        with Errors():
            if e:
                raise e
        self.stop = True
        self.thread.join()

    def do_pause(self, val=None):
        if val is None:
            self.pause = not self.pause
        else:
            self.pause = bool(v)

    def tag(self, name, attrs):
        if name == "pause":
            self.do_pause(True)
        elif name == "play":
            self.do_pause(False)
        else:
            super().tag(name, attrs)

    def inner(self):
        e = ellipsis(self.len)
        for _ in e:
            if self.stop:
                break
            while self.pause and not self.stop:
                pass
            time.sleep(self.dur)


scope = [BaseHandle({})]
widgets = []


class OddoutParser(HTMLParser):
    def handle_starttag(self: HTMLParser, name: str, args: list[tuple[str]]):
        scope[-1].starttag(name, dict(args))

    def handle_endtag(self: HTMLParser, name: str):
        scope[-1].endtag(name)

    def handle_data(self, data):
        scope[-1].data(data)

    def handel_startendtag(self, name, attrs):
        scope[-1].tag(name, attrs)

    def handle_pi(self, text):
        if text[0] == '=':
            with Errors():
                print(eval(text[1:]))
        else:
            exec(text, globals(), locals())


parser = OddoutParser()


def oddout(data):
    parser.feed(data)



"""oddout('''\
<ellipsis>
    <?="hello world">
    <?time.sleep(2)>
    <?="hello world again">
    <?time.sleep(2)>
</ellipsis>
''')"""

r = ProgressBar.register(max=100)
next(r)
for i in range(100):
    print(r.send(i))
    time.sleep(1)
