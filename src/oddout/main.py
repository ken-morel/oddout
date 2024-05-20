import contextlib
import sys

import functools
import threading
import shutil
import time

from html.parser import HTMLParser
from typing import Any

from colorama import *

init()
width, height = shutil.get_terminal_size()


def update_terminal_sizes():
    global width, height
    width, height = shutil.get_terminal_size()


class FakeStdout:
    write = sys.stdout.write



fake_stdout = FakeStdout()
_print  = functools.partial(print, file=fake_stdout)


def em(text, border_color="green", text_color="white"):
    f_b = Fore(border_color)
    f_r = Fore("reset")
    f_t = Fore(text_color)
    text = textwrap.wrap(text, width-2)
    mw = max(map(len, text))
    lo = (width - 1 - mw) // 2
    _print(f_b+width*'─')
    for ln in text:
        ln = '> '+ln+';'
        _print(f_t+lo*' '+ln)
    _print(f_b+width*'─')

def error(e):
    em(
        e.__class__.__name__+": "+str(e),
        border_color="red",
        text_color = "red"
    )

def ellipsis(le=3, ch='.', s =' '):
    i = 0
    _print("   ", end="")
    while True:
        yield
        i += 1
        i %= (le+1)
        _print("\b\b\b"+(i*ch).ljust(le, s), end="")


@contextlib.contextmanager
def Errors():
    try:
        yield error
    except Exception as e:
        error(e)

class BaseHandle:
    sub_handles = []
    child: Any = None

    def __enter__(self):
        pass

    def __leave__(self, e):
        pass

    def __init__(self, attrs):
        self.attrs = attrs
        self.__enter__()

    def __init_subclass__(cls):
        BaseHandle.sub_handles.append(cls)

    def starttag(self, name, attrs):
        for handle in BaseHandle.sub_handles:
            if handle.name == name:
                sub = handle(attrs)
                self.child = sub
                scope.append(sub)

    def endtag(self, name):
        if name == self.name:
            for _ in range(len(scope) - scope.index(self)):
                scope.pop()
            self.__leave__()
    def tag(self, name, attrs):
        pass
###############################################################################
class ProgressBar(BaseHandle):
    name = "progressbar"
    def __enter__(self):
        self.t = time.perf_counter()
        self.lastSpeed = self.calls = self.last = self.lastVal = 0
        self.alpha = float(self.attrs.get(alpha), 0.3)
        self.max = float(self.attrs.get(max), 100)
        self.procs = {}
        self.main_proc_name = self.attrs.get("name", "main")

    def tag(self, name, attrs):
        if name == "progress":
            proc_name = attrs.get("proc", self.main_proc_name)
            try:
                val = attrs["value"]
            except IndexError:
                return error(ValueError("Called progress without specifying value"))
            self.procs[proc_name] = val
        self.update()
    def update(self, char='-'):
        update_terminal_sizes()

        vals = []

        i = 0
        for x in others:
            i += 1
            if isinstance(x, tuple) and len(x) >= 2:
                m, c = x[0], x[1]
                msg = x[2] if len(x) >= 3 else 'proc %d'%i
                vals.append((m, Fore(c), msg))
        assert per <= self.max
        self.calls += 1
        t2 = time.perf_counter()
        dt = t2-self.t
        ds = per - self.lastVal
        speed = ds/dt
        a, b = self.alpha, 1-self.alpha
        self.last = a * speed + b * self.last
        speed = self.last / (1 - b ** self.calls) if self.calls else self.last
        if speed > 0:
            t = (self.max - per) / speed
            m = t // 60
            s = t // 1 % 60
            cs = (t*100) // 1 % 100
            remain = f"{int(m):02d}:{int(s):02d}:{int(cs):02d}"
        else:
            remain = "  :  :  "
        mw = width - 20


        lv = sum(x[0] for x in vals)


        assert lv <= per, "sum of rest: %d is more than: %d"%(lv, p)
        vals.append((per- lv, Fore("reset"), "main"))
        txt = f"\r{Fore('BLUE')}["
        for length, color, _ in vals:
            txt += color + int(
                length/self.max*mw
            )*char + Fore(
                "reset"
            )
        txt += ' '*(mw-txt.count('-'))
        print(txt + f"{Fore('blue')}]{Fore()} {int(per/self.max*100):02d}% eta {remain}",end="\r")
        for i, c in enumerate(vals):
            length, color, msg = c
            if msg == "main":
                length = per
            print(Cursor.DOWN(1), color+msg+": "+format(float(length), '.2f'), end="\r")
        self.height = i+2
        print(Cursor.UP(i+1), end="")

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
            super().tag(name,attrs)

    def inner(self, ):
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
        _print(data)

    def handel_startendtag(self, name, attrs):
        scope[-1].tag(name, attrs)

def wrap():
    global orig_stdout
    parser = OddoutParser()
    orig_stdout_write = sys.stdout.write
    sys.stdout.write = parser.feed


wrap()

