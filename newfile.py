import shutil, textwrap, time, contextlib, threading
from colorama import *
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
