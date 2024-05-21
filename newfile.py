#############################
############win32#############
#############################

# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.

# from winbase.h
STDOUT = -11
STDERR = -12

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

try:
    import ctypes
    from ctypes import LibraryLoader
    windll = LibraryLoader(ctypes.WinDLL)
    from ctypes import wintypes
except (AttributeError, ImportError):
    windll = None
    SetConsoleTextAttribute = lambda *_: None
    winapi_test = lambda *_: None
else:
    from ctypes import byref, Structure, c_char, POINTER

    COORD = wintypes._COORD

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
        """struct in wincon.h."""
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wintypes.WORD),
            ("srWindow", wintypes.SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]
        def __str__(self):
            return '(%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)' % (
                self.dwSize.Y, self.dwSize.X
                , self.dwCursorPosition.Y, self.dwCursorPosition.X
                , self.wAttributes
                , self.srWindow.Top, self.srWindow.Left, self.srWindow.Bottom, self.srWindow.Right
                , self.dwMaximumWindowSize.Y, self.dwMaximumWindowSize.X
            )

    _GetStdHandle = windll.kernel32.GetStdHandle
    _GetStdHandle.argtypes = [
        wintypes.DWORD,
    ]
    _GetStdHandle.restype = wintypes.HANDLE

    _GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    _GetConsoleScreenBufferInfo.argtypes = [
        wintypes.HANDLE,
        POINTER(CONSOLE_SCREEN_BUFFER_INFO),
    ]
    _GetConsoleScreenBufferInfo.restype = wintypes.BOOL

    _SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    _SetConsoleTextAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
    ]
    _SetConsoleTextAttribute.restype = wintypes.BOOL

    _SetConsoleCursorPosition = windll.kernel32.SetConsoleCursorPosition
    _SetConsoleCursorPosition.argtypes = [
        wintypes.HANDLE,
        COORD,
    ]
    _SetConsoleCursorPosition.restype = wintypes.BOOL

    _FillConsoleOutputCharacterA = windll.kernel32.FillConsoleOutputCharacterA
    _FillConsoleOutputCharacterA.argtypes = [
        wintypes.HANDLE,
        c_char,
        wintypes.DWORD,
        COORD,
        POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputCharacterA.restype = wintypes.BOOL

    _FillConsoleOutputAttribute = windll.kernel32.FillConsoleOutputAttribute
    _FillConsoleOutputAttribute.argtypes = [
        wintypes.HANDLE,
        wintypes.WORD,
        wintypes.DWORD,
        COORD,
        POINTER(wintypes.DWORD),
    ]
    _FillConsoleOutputAttribute.restype = wintypes.BOOL

    _SetConsoleTitleW = windll.kernel32.SetConsoleTitleW
    _SetConsoleTitleW.argtypes = [
        wintypes.LPCWSTR
    ]
    _SetConsoleTitleW.restype = wintypes.BOOL

    _GetConsoleMode = windll.kernel32.GetConsoleMode
    _GetConsoleMode.argtypes = [
        wintypes.HANDLE,
        POINTER(wintypes.DWORD)
    ]
    _GetConsoleMode.restype = wintypes.BOOL

    _SetConsoleMode = windll.kernel32.SetConsoleMode
    _SetConsoleMode.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD
    ]
    _SetConsoleMode.restype = wintypes.BOOL

    def _winapi_test(handle):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        success = _GetConsoleScreenBufferInfo(
            handle, byref(csbi))
        return bool(success)

    def winapi_test():
        return any(_winapi_test(h) for h in
                   (_GetStdHandle(STDOUT), _GetStdHandle(STDERR)))

    def GetConsoleScreenBufferInfo(stream_id=STDOUT):
        handle = _GetStdHandle(stream_id)
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        success = _GetConsoleScreenBufferInfo(
            handle, byref(csbi))
        return csbi

    def SetConsoleTextAttribute(stream_id, attrs):
        handle = _GetStdHandle(stream_id)
        return _SetConsoleTextAttribute(handle, attrs)

    def SetConsoleCursorPosition(stream_id, position, adjust=True):
        position = COORD(*position)
        # If the position is out of range, do nothing.
        if position.Y <= 0 or position.X <= 0:
            return
        # Adjust for Windows' SetConsoleCursorPosition:
        #    1. being 0-based, while ANSI is 1-based.
        #    2. expecting (x,y), while ANSI uses (y,x).
        adjusted_position = COORD(position.Y - 1, position.X - 1)
        if adjust:
            # Adjust for viewport's scroll position
            sr = GetConsoleScreenBufferInfo(STDOUT).srWindow
            adjusted_position.Y += sr.Top
            adjusted_position.X += sr.Left
        # Resume normal processing
        handle = _GetStdHandle(stream_id)
        return _SetConsoleCursorPosition(handle, adjusted_position)

    def FillConsoleOutputCharacter(stream_id, char, length, start):
        handle = _GetStdHandle(stream_id)
        char = c_char(char.encode())
        length = wintypes.DWORD(length)
        num_written = wintypes.DWORD(0)
        # Note that this is hard-coded for ANSI (vs wide) bytes.
        success = _FillConsoleOutputCharacterA(
            handle, char, length, start, byref(num_written))
        return num_written.value

    def FillConsoleOutputAttribute(stream_id, attr, length, start):
        ''' FillConsoleOutputAttribute( hConsole, csbi.wAttributes, dwConSize, coordScreen, &cCharsWritten )'''
        handle = _GetStdHandle(stream_id)
        attribute = wintypes.WORD(attr)
        length = wintypes.DWORD(length)
        num_written = wintypes.DWORD(0)
        # Note that this is hard-coded for ANSI (vs wide) bytes.
        return _FillConsoleOutputAttribute(
            handle, attribute, length, start, byref(num_written))

    def SetConsoleTitle(title):
        return _SetConsoleTitleW(title)

    def GetConsoleMode(handle):
        mode = wintypes.DWORD()
        success = _GetConsoleMode(handle, byref(mode))
        if not success:
            raise ctypes.WinError()
        return mode.value

    def SetConsoleMode(handle, mode):
        success = _SetConsoleMode(handle, mode)
        if not success:
            raise ctypes.WinError()


#############################
###########winterm############
#############################
# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
try:
    from msvcrt import get_osfhandle
except ImportError:
    def get_osfhandle(_):
        raise OSError("This isn't windows!")


##from . import win32

# from wincon.h
class WinColor(object):
    BLACK   = 0
    BLUE    = 1
    GREEN   = 2
    CYAN    = 3
    RED     = 4
    MAGENTA = 5
    YELLOW  = 6
    GREY    = 7

# from wincon.h
class WinStyle(object):
    NORMAL              = 0x00 # dim text, dim background
    BRIGHT              = 0x08 # bright text, dim background
    BRIGHT_BACKGROUND   = 0x80 # dim text, bright background

class WinTerm(object):

    def __init__(self):
        self._default = win32.GetConsoleScreenBufferInfo(win32.STDOUT).wAttributes
        self.set_attrs(self._default)
        self._default_fore = self._fore
        self._default_back = self._back
        self._default_style = self._style
        # In order to emulate LIGHT_EX in windows, we borrow the BRIGHT style.
        # So that LIGHT_EX colors and BRIGHT style do not clobber each other,
        # we track them separately, since LIGHT_EX is overwritten by Fore/Back
        # and BRIGHT is overwritten by Style codes.
        self._light = 0

    def get_attrs(self):
        return self._fore + self._back * 16 + (self._style | self._light)

    def set_attrs(self, value):
        self._fore = value & 7
        self._back = (value >> 4) & 7
        self._style = value & (WinStyle.BRIGHT | WinStyle.BRIGHT_BACKGROUND)

    def reset_all(self, on_stderr=None):
        self.set_attrs(self._default)
        self.set_console(attrs=self._default)
        self._light = 0

    def fore(self, fore=None, light=False, on_stderr=False):
        if fore is None:
            fore = self._default_fore
        self._fore = fore
        # Emulate LIGHT_EX with BRIGHT Style
        if light:
            self._light |= WinStyle.BRIGHT
        else:
            self._light &= ~WinStyle.BRIGHT
        self.set_console(on_stderr=on_stderr)

    def back(self, back=None, light=False, on_stderr=False):
        if back is None:
            back = self._default_back
        self._back = back
        # Emulate LIGHT_EX with BRIGHT_BACKGROUND Style
        if light:
            self._light |= WinStyle.BRIGHT_BACKGROUND
        else:
            self._light &= ~WinStyle.BRIGHT_BACKGROUND
        self.set_console(on_stderr=on_stderr)

    def style(self, style=None, on_stderr=False):
        if style is None:
            style = self._default_style
        self._style = style
        self.set_console(on_stderr=on_stderr)

    def set_console(self, attrs=None, on_stderr=False):
        if attrs is None:
            attrs = self.get_attrs()
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        win32.SetConsoleTextAttribute(handle, attrs)

    def get_position(self, handle):
        position = win32.GetConsoleScreenBufferInfo(handle).dwCursorPosition
        # Because Windows coordinates are 0-based,
        # and win32.SetConsoleCursorPosition expects 1-based.
        position.X += 1
        position.Y += 1
        return position

    def set_cursor_position(self, position=None, on_stderr=False):
        if position is None:
            # I'm not currently tracking the position, so there is no default.
            # position = self.get_position()
            return
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        win32.SetConsoleCursorPosition(handle, position)

    def cursor_adjust(self, x, y, on_stderr=False):
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        position = self.get_position(handle)
        adjusted_position = (position.Y + y, position.X + x)
        win32.SetConsoleCursorPosition(handle, adjusted_position, adjust=False)

    def erase_screen(self, mode=0, on_stderr=False):
        # 0 should clear from the cursor to the end of the screen.
        # 1 should clear from the cursor to the beginning of the screen.
        # 2 should clear the entire screen, and move cursor to (1,1)
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        csbi = win32.GetConsoleScreenBufferInfo(handle)
        # get the number of character cells in the current buffer
        cells_in_screen = csbi.dwSize.X * csbi.dwSize.Y
        # get number of character cells before current cursor position
        cells_before_cursor = csbi.dwSize.X * csbi.dwCursorPosition.Y + csbi.dwCursorPosition.X
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = cells_in_screen - cells_before_cursor
        elif mode == 1:
            from_coord = win32.COORD(0, 0)
            cells_to_erase = cells_before_cursor
        elif mode == 2:
            from_coord = win32.COORD(0, 0)
            cells_to_erase = cells_in_screen
        else:
            # invalid mode
            return
        # fill the entire screen with blanks
        win32.FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        # now set the buffer's attributes accordingly
        win32.FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)
        if mode == 2:
            # put the cursor where needed
            win32.SetConsoleCursorPosition(handle, (1, 1))

    def erase_line(self, mode=0, on_stderr=False):
        # 0 should clear from the cursor to the end of the line.
        # 1 should clear from the cursor to the beginning of the line.
        # 2 should clear the entire line.
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        csbi = win32.GetConsoleScreenBufferInfo(handle)
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = csbi.dwSize.X - csbi.dwCursorPosition.X
        elif mode == 1:
            from_coord = win32.COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwCursorPosition.X
        elif mode == 2:
            from_coord = win32.COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwSize.X
        else:
            # invalid mode
            return
        # fill the entire screen with blanks
        win32.FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        # now set the buffer's attributes accordingly
        win32.FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)

    def set_title(self, title):
        win32.SetConsoleTitle(title)


def enable_vt_processing(fd):
    if win32.windll is None or not win32.winapi_test():
        return False

    try:
        handle = get_osfhandle(fd)
        mode = win32.GetConsoleMode(handle)
        win32.SetConsoleMode(
            handle,
            mode | win32.ENABLE_VIRTUAL_TERMINAL_PROCESSING,
        )

        mode = win32.GetConsoleMode(handle)
        if mode & win32.ENABLE_VIRTUAL_TERMINAL_PROCESSING:
            return True
    # Can get TypeError in testsuite where 'fd' is a Mock()
    except (OSError, TypeError):
        return False


#############################
############ansi##############
#############################
# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
'''
This module generates ANSI character codes to printing colors to terminals.
See: http://en.wikipedia.org/wiki/ANSI_escape_code
'''



#############################
#########ansitowin32###########
#############################
# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import re
import sys
import os

##from .ansi import AnsiFore, AnsiBack, AnsiStyle, Style, BEL
##from .winterm import enable_vt_processing, WinTerm, WinColor, WinStyle
##from .win32 import windll, winapi_test


winterm = None
if windll is not None:
    winterm = WinTerm()


class StreamWrapper(object):
    '''
    Wraps a stream (such as stdout), acting as a transparent proxy for all
    attribute access apart from method 'write()', which is delegated to our
    Converter instance.
    '''
    def __init__(self, wrapped, converter):
        # double-underscore everything to prevent clashes with names of
        # attributes on the wrapped stream object.
        self.__wrapped = wrapped
        self.__convertor = converter

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

    def __enter__(self, *args, **kwargs):
        # special method lookup bypasses __getattr__/__getattribute__, see
        # https://stackoverflow.com/questions/12632894/why-doesnt-getattr-work-with-exit
        # thus, contextlib magic methods are not proxied via __getattr__
        return self.__wrapped.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self.__wrapped.__exit__(*args, **kwargs)

    def __setstate__(self, state):
        self.__dict__ = state

    def __getstate__(self):
        return self.__dict__

    def write(self, text):
        self.__convertor.write(text)

    def isatty(self):
        stream = self.__wrapped
        if 'PYCHARM_HOSTED' in os.environ:
            if stream is not None and (stream is sys.__stdout__ or stream is sys.__stderr__):
                return True
        try:
            stream_isatty = stream.isatty
        except AttributeError:
            return False
        else:
            return stream_isatty()

    @property
    def closed(self):
        stream = self.__wrapped
        try:
            return stream.closed
        # AttributeError in the case that the stream doesn't support being closed
        # ValueError for the case that the stream has already been detached when atexit runs
        except (AttributeError, ValueError):
            return True


class AnsiToWin32(object):
    '''
    Implements a 'write()' method which, on Windows, will strip ANSI character
    sequences from the text, and if outputting to a tty, will convert them into
    win32 function calls.
    '''
    ANSI_CSI_RE = re.compile('\001?\033\\[((?:\\d|;)*)([a-zA-Z])\002?')   # Control Sequence Introducer
    ANSI_OSC_RE = re.compile('\001?\033\\]([^\a]*)(\a)\002?')             # Operating System Command

    def __init__(self, wrapped, convert=None, strip=None, autoreset=False):
        # The wrapped stream (normally sys.stdout or sys.stderr)
        self.wrapped = wrapped

        # should we reset colors to defaults after every .write()
        self.autoreset = autoreset

        # create the proxy wrapping our output stream
        self.stream = StreamWrapper(wrapped, self)

        on_windows = os.name == 'nt'
        # We test if the WinAPI works, because even if we are on Windows
        # we may be using a terminal that doesn't support the WinAPI
        # (e.g. Cygwin Terminal). In this case it's up to the terminal
        # to support the ANSI codes.
        conversion_supported = on_windows and winapi_test()
        try:
            fd = wrapped.fileno()
        except Exception:
            fd = -1
        system_has_native_ansi = not on_windows or enable_vt_processing(fd)
        have_tty = not self.stream.closed and self.stream.isatty()
        need_conversion = conversion_supported and not system_has_native_ansi

        # should we strip ANSI sequences from our output?
        if strip is None:
            strip = need_conversion or not have_tty
        self.strip = strip

        # should we should convert ANSI sequences into win32 calls?
        if convert is None:
            convert = need_conversion and have_tty
        self.convert = convert

        # dict of ansi codes to win32 functions and parameters
        self.win32_calls = self.get_win32_calls()

        # are we wrapping stderr?
        self.on_stderr = self.wrapped is sys.stderr

    def should_wrap(self):
        '''
        True if this class is actually needed. If false, then the output
        stream will not be affected, nor will win32 calls be issued, so
        wrapping stdout is not actually required. This will generally be
        False on non-Windows platforms, unless optional functionality like
        autoreset has been requested using kwargs to init()
        '''
        return self.convert or self.strip or self.autoreset

    def get_win32_calls(self):
        if self.convert and winterm:
            return {
                AnsiStyle.RESET_ALL: (winterm.reset_all, ),
                AnsiStyle.BRIGHT: (winterm.style, WinStyle.BRIGHT),
                AnsiStyle.DIM: (winterm.style, WinStyle.NORMAL),
                AnsiStyle.NORMAL: (winterm.style, WinStyle.NORMAL),
                AnsiFore.BLACK: (winterm.fore, WinColor.BLACK),
                AnsiFore.RED: (winterm.fore, WinColor.RED),
                AnsiFore.GREEN: (winterm.fore, WinColor.GREEN),
                AnsiFore.YELLOW: (winterm.fore, WinColor.YELLOW),
                AnsiFore.BLUE: (winterm.fore, WinColor.BLUE),
                AnsiFore.MAGENTA: (winterm.fore, WinColor.MAGENTA),
                AnsiFore.CYAN: (winterm.fore, WinColor.CYAN),
                AnsiFore.WHITE: (winterm.fore, WinColor.GREY),
                AnsiFore.RESET: (winterm.fore, ),
                AnsiFore.LIGHTBLACK_EX: (winterm.fore, WinColor.BLACK, True),
                AnsiFore.LIGHTRED_EX: (winterm.fore, WinColor.RED, True),
                AnsiFore.LIGHTGREEN_EX: (winterm.fore, WinColor.GREEN, True),
                AnsiFore.LIGHTYELLOW_EX: (winterm.fore, WinColor.YELLOW, True),
                AnsiFore.LIGHTBLUE_EX: (winterm.fore, WinColor.BLUE, True),
                AnsiFore.LIGHTMAGENTA_EX: (winterm.fore, WinColor.MAGENTA, True),
                AnsiFore.LIGHTCYAN_EX: (winterm.fore, WinColor.CYAN, True),
                AnsiFore.LIGHTWHITE_EX: (winterm.fore, WinColor.GREY, True),
                AnsiBack.BLACK: (winterm.back, WinColor.BLACK),
                AnsiBack.RED: (winterm.back, WinColor.RED),
                AnsiBack.GREEN: (winterm.back, WinColor.GREEN),
                AnsiBack.YELLOW: (winterm.back, WinColor.YELLOW),
                AnsiBack.BLUE: (winterm.back, WinColor.BLUE),
                AnsiBack.MAGENTA: (winterm.back, WinColor.MAGENTA),
                AnsiBack.CYAN: (winterm.back, WinColor.CYAN),
                AnsiBack.WHITE: (winterm.back, WinColor.GREY),
                AnsiBack.RESET: (winterm.back, ),
                AnsiBack.LIGHTBLACK_EX: (winterm.back, WinColor.BLACK, True),
                AnsiBack.LIGHTRED_EX: (winterm.back, WinColor.RED, True),
                AnsiBack.LIGHTGREEN_EX: (winterm.back, WinColor.GREEN, True),
                AnsiBack.LIGHTYELLOW_EX: (winterm.back, WinColor.YELLOW, True),
                AnsiBack.LIGHTBLUE_EX: (winterm.back, WinColor.BLUE, True),
                AnsiBack.LIGHTMAGENTA_EX: (winterm.back, WinColor.MAGENTA, True),
                AnsiBack.LIGHTCYAN_EX: (winterm.back, WinColor.CYAN, True),
                AnsiBack.LIGHTWHITE_EX: (winterm.back, WinColor.GREY, True),
            }
        return dict()

    def write(self, text):
        if self.strip or self.convert:
            self.write_and_convert(text)
        else:
            self.wrapped.write(text)
            self.wrapped.flush()
        if self.autoreset:
            self.reset_all()


    def reset_all(self):
        if self.convert:
            self.call_win32('m', (0,))
        elif not self.strip and not self.stream.closed:
            self.wrapped.write(Style.RESET_ALL)


    def write_and_convert(self, text):
        '''
        Write the given text to our wrapped stream, stripping any ANSI
        sequences from the text, and optionally converting them into win32
        calls.
        '''
        cursor = 0
        text = self.convert_osc(text)
        for match in self.ANSI_CSI_RE.finditer(text):
            start, end = match.span()
            self.write_plain_text(text, cursor, start)
            self.convert_ansi(*match.groups())
            cursor = end
        self.write_plain_text(text, cursor, len(text))


    def write_plain_text(self, text, start, end):
        if start < end:
            self.wrapped.write(text[start:end])
            self.wrapped.flush()


    def convert_ansi(self, paramstring, command):
        if self.convert:
            params = self.extract_params(command, paramstring)
            self.call_win32(command, params)


    def extract_params(self, command, paramstring):
        if command in 'Hf':
            params = tuple(int(p) if len(p) != 0 else 1 for p in paramstring.split(';'))
            while len(params) < 2:
                # defaults:
                params = params + (1,)
        else:
            params = tuple(int(p) for p in paramstring.split(';') if len(p) != 0)
            if len(params) == 0:
                # defaults:
                if command in 'JKm':
                    params = (0,)
                elif command in 'ABCD':
                    params = (1,)

        return params


    def call_win32(self, command, params):
        if command == 'm':
            for param in params:
                if param in self.win32_calls:
                    func_args = self.win32_calls[param]
                    func = func_args[0]
                    args = func_args[1:]
                    kwargs = dict(on_stderr=self.on_stderr)
                    func(*args, **kwargs)
        elif command in 'J':
            winterm.erase_screen(params[0], on_stderr=self.on_stderr)
        elif command in 'K':
            winterm.erase_line(params[0], on_stderr=self.on_stderr)
        elif command in 'Hf':     # cursor position - absolute
            winterm.set_cursor_position(params, on_stderr=self.on_stderr)
        elif command in 'ABCD':   # cursor position - relative
            n = params[0]
            # A - up, B - down, C - forward, D - back
            x, y = {'A': (0, -n), 'B': (0, n), 'C': (n, 0), 'D': (-n, 0)}[command]
            winterm.cursor_adjust(x, y, on_stderr=self.on_stderr)


    def convert_osc(self, text):
        for match in self.ANSI_OSC_RE.finditer(text):
            start, end = match.span()
            text = text[:start] + text[end:]
            paramstring, command = match.groups()
            if command == BEL:
                if paramstring.count(";") == 1:
                    params = paramstring.split(";")
                    # 0 - change title and icon (we will only change title)
                    # 1 - change icon (we don't support this)
                    # 2 - change title
                    if params[0] in '02':
                        winterm.set_title(params[1])
        return text


    def flush(self):
        self.wrapped.flush()

##############################
###########initialize#############
##############################

# Copyright Jonathan Hartley 2013. BSD 3-Clause license, see LICENSE file.
import atexit
import contextlib
import sys

##from .ansitowin32 import AnsiToWin32


def _wipe_internal_state_for_tests():
    global orig_stdout, orig_stderr
    orig_stdout = None
    orig_stderr = None

    global wrapped_stdout, wrapped_stderr
    wrapped_stdout = None
    wrapped_stderr = None

    global atexit_done
    atexit_done = False

    global fixed_windows_console
    fixed_windows_console = False

    try:
        # no-op if it wasn't registered
        atexit.unregister(reset_all)
    except AttributeError:
        # python 2: no atexit.unregister. Oh well, we did our best.
        pass


def reset_all():
    if AnsiToWin32 is not None:    # Issue #74: objects might become None at exit
        AnsiToWin32(orig_stdout).reset_all()


def init(autoreset=False, convert=None, strip=None, wrap=True):

    if not wrap and any([autoreset, convert, strip]):
        raise ValueError('wrap=False conflicts with any other arg=True')

    global wrapped_stdout, wrapped_stderr
    global orig_stdout, orig_stderr

    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    if sys.stdout is None:
        wrapped_stdout = None
    else:
        sys.stdout = wrapped_stdout = \
            wrap_stream(orig_stdout, convert, strip, autoreset, wrap)
    if sys.stderr is None:
        wrapped_stderr = None
    else:
        sys.stderr = wrapped_stderr = \
            wrap_stream(orig_stderr, convert, strip, autoreset, wrap)

    global atexit_done
    if not atexit_done:
        atexit.register(reset_all)
        atexit_done = True


def deinit():
    if orig_stdout is not None:
        sys.stdout = orig_stdout
    if orig_stderr is not None:
        sys.stderr = orig_stderr


def just_fix_windows_console():
    global fixed_windows_console

    if sys.platform != "win32":
        return
    if fixed_windows_console:
        return
    if wrapped_stdout is not None or wrapped_stderr is not None:
        # Someone already ran init() and it did stuff, so we won't second-guess them
        return

    # On newer versions of Windows, AnsiToWin32.__init__ will implicitly enable the
    # native ANSI support in the console as a side-effect. We only need to actually
    # replace sys.stdout/stderr if we're in the old-style conversion mode.
    new_stdout = AnsiToWin32(sys.stdout, convert=None, strip=None, autoreset=False)
    if new_stdout.convert:
        sys.stdout = new_stdout
    new_stderr = AnsiToWin32(sys.stderr, convert=None, strip=None, autoreset=False)
    if new_stderr.convert:
        sys.stderr = new_stderr

    fixed_windows_console = True

@contextlib.contextmanager
def colorama_text(*args, **kwargs):
    init(*args, **kwargs)
    try:
        yield
    finally:
        deinit()


def reinit():
    if wrapped_stdout is not None:
        sys.stdout = wrapped_stdout
    if wrapped_stderr is not None:
        sys.stderr = wrapped_stderr


def wrap_stream(stream, convert, strip, autoreset, wrap):
    if wrap:
        wrapper = AnsiToWin32(stream,
            convert=convert, strip=strip, autoreset=autoreset)
        if wrapper.should_wrap():
            stream = wrapper.stream
    return stream


# Use this for initial setup as well, to reduce code duplication
_wipe_internal_state_for_tests()

#__________________________________________
#__________________________________________


import shutil, textwrap, time, contextlib, threading

def fmtSize(byt):
    if byt < 1:
        return '%f b'%byt*8
    elif byt < 1_000:
        return '%f B'%byt
    elif byt < 1_000_000:
        return '%f kB'%(byt/1_000)
    else:
        return '%f MB'%(byt/1_000_000)

width, height = shutil.get_terminal_size()
def update_terminal_sizes():
    global width, height
    width, height = shutil.get_terminal_size()
indent = 0
def getD():
    return time.perf_counter()*1_000-logT
def goto(side=None):
    global indent
    if side is True:
        indent += 1
    elif side is False:
        indent -= 1
def inner(n=1):
    [goto(True) for _ in range(n)]
def outer(n=1):
    [goto(False) for _ in range(n)]
    
    
logT = time.perf_counter()*1_000
def log(*data, go=None, sep=' ', end='\n'):
    global logT
    ct = time.perf_counter()*1_000
    dt = ct-logT
    logT = ct
    h = '@'+('%05dms; '%dt)
    print(h, end='')
    if go is False:
        goto(go)
    st = sep.join(map(str, data))
    fl, *rl = textwrap.wrap(st, width-7)
    txt = "\n".join([indent*"  "+fl]+[indent*"  "+"        | "+ln for ln in rl])
    print(txt, end=end)
    if go is True:
        goto(go)
    return dt
#╭╯╰╮—|
def box(txt, border_color="green", text_color="white"):
    f_b = Fore(border_color)
    f_r = Fore("reset")
    f_t = Fore(text_color)
    
    text = []
    [text.extend(textwrap.wrap(line, width-2)) for line in txt.splitlines()]
    mw = max(map(len, text))
    lo = (width - 2 - mw) // 2
    print((lo*' ')+f_b+'╭'+(mw*'—')+'╮'+f_r)
    for ln in text:
        print((lo*' ')+f_b+'|'+f_r+f_t+ln.center(mw, ' ')+f_b+'|'+f_r)
    print((lo*' ')+f_b+'╰'+(mw*'—')+'╯'+f_r)
def center(text, ch=" "):
    print(text.center(width, ch))
def hr(text=None, ch='—'):
    if text:
        center(text)
    print(width*ch)
def ellipsis(le=3, ch='.', s =' '):
    i = 0
    print(le*s, end=le*"\b")
    while True:
        yield
        i += 1
        i %= (le+1)
        print((i*ch).ljust(le, s), end=le*"\b")
        
@contextlib.contextmanager
def Ellipsis(l=3, d=0.5):
    stop = False
    pause = False
    def do_pause(v=None):
        nonlocal pause
        if v is None:
            pause = not pause
        else:
            pause = bool(v)
    def inner():
        e = ellipsis(l)
        for _ in e:
            if stop:
                break
            while pause and not stop:
                pass
            time.sleep(d)
    t = threading.Thread(target=inner)
    t.start()
    with Errors():
        yield do_pause
    stop = True
    t.join()
    print()
    
#╭╯╰╮—|
raw_input = input
def input(q="> ", border_color="green", text_color="white", margin = 1):
    f_b = Fore(border_color)
    f_r = Fore("reset")
    f_t = Fore(text_color)
    
    text = []
    [text.extend(textwrap.wrap(line, width-2*margin-2)) for line in q.splitlines()]
    mw = width - 4 - 2*margin
    lo = (width - mw - margin - 2) // 2
    print((lo*' ')+f_b+'╭'+(mw*'─')+'╮'+f_r)
    for ln in text:
        print((lo*' ')+f_b+'|'+f_r+f_t+ln.ljust(mw, ' ')+f_b+'|'+f_r)
    print((lo*' ')+f_b+'╰'+(mw*'─')+'╯'+f_r, end="\r")
    print(Cursor.UP(1)+Cursor.FORWARD(lo+2+len(text[-1])), end="")
    txt = raw_input()
    print(Cursor.DOWN(2), end="\r")
    return txt
    
        
    
def em(text, border_color="green", text_color="white"):
    f_b = Fore(border_color)
    f_r = Fore("reset")
    f_t = Fore(text_color)
    
    
    text = textwrap.wrap(text, width-2)
    mw = max(map(len, text))
    lo = (width - 1 - mw) // 2
    print(f_b+width*'─')
    for ln in text:
        ln = '> '+ln+';'
        print(f_t+lo*' '+ln)
    print(f_b+width*'─')

def error(e):
    em(
        e.__class__.__name__+": "+str(e),
        border_color="red",
        text_color = "red"
    )
    


@contextlib.contextmanager
def Errors():
    try:
        yield error
    except Exception as e:
        error(e)
formats = {
    'info': Fore("blue")+"[*]"+Fore()+ " %s",
    'add': Fore("cyan")+"[+]"+Fore()+" %s",
    'note': Fore("magenta")+"  >"+Fore()+" %s",
    'subst': Fore("red")+"[-]"+Fore()+" %s",
    'cross': Fore("red")+"[×]"+Fore()+" %s",
    'none': "    %s"
}
def fmt(txt, style=None):
    return formats.get(
        style,
        formats.get(
            "none",
            "%s"
        )
    )

#chars = ['×','╰', '─']
class ProgressBar():
    def __init__(self, max=100, alpha=0.3):
        self.t = time.perf_counter()
        self.lastSpeed = self.calls = self.last = self.lastVal = 0
        self.alpha = alpha
        self.max = max
        #print()
        
    def __call__(self, per, *others, char='-'):
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
    def __del__(self):
        print(Cursor.DOWN(self.height), end="\r")
    exit = __exit__ = __del__
    


init(autoreset=True)

if __name__ == "__main__":
    hr("log")
    
    fmt("info\ninfo2", 'info')
    fmt("add\nadd2", 'add')
    fmt("info\nnote2", "note")
    fmt("log\nlog2", "log")
    
    hr("ellipsis")
    with Ellipsis() as p:
        time.sleep(2)
        p()
        print("pause")
        time.sleep(2)
        p()
        time.sleep(2)
    hr("em")
    em("hello world")

    hr("box")
    box("gft trft")
    hr("error")
    with Errors():
        raise ValueError(45)
    hr("input&ellipsis")
    with Ellipsis():
        name = input("name!: ")
    n = len(name)
    print("helli", name, "has:")
    prog = ProgressBar(100)
    hr("progress")
    for x in range(101):
        prog(x, (x/2, "red", "bad"), (x/3, "green", "goog"))
        time.sleep(0.1)
    del prog
    print("letters")

        
__all__ = ["fmtSize", "update_terminal_size"]
