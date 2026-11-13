#!/usr/bin/env python3
"""In-terminal video player for kitty: ffmpeg decodes, frames go over the kitty graphics protocol, ffplay plays the
sound. Fills the terminal keeping the aspect ratio and starts at once (no conversion step).
Keys: space pause/resume · left/right seek 5 s · j/l or shift+left/right or down/up seek 10 s · 0..9 jump to 0..90 % ·
o open in system player · q/Esc/Enter close.   Mouse: click = pause, double click left/right third = -10/+10 s,
click on the bottom bar = seek."""
import base64, fcntl, os, re, select, signal, struct, subprocess, sys, termios, time, tty, zlib

FPS = 15
PIXEL_BUDGET = 450_000  # decoded pixels per frame; kitty scales it up to the terminal area
path = sys.argv[1]
DEVNULL = subprocess.DEVNULL


def probe():
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:stream_tags=rotate:format=duration",
                          "-of", "default=nw=1", path], capture_output=True, text=True).stdout
    w = h = rot = 0
    dur = 0.0
    for line in out.splitlines():
        k, _, v = line.partition("=")
        try:
            if k == "width": w = int(v)
            elif k == "height": h = int(v)
            elif k in ("rotation", "rotate"): rot = int(float(v))
            elif k == "duration": dur = float(v)
        except ValueError:
            pass
    if abs(rot) % 180 == 90: w, h = h, w  # ffmpeg autorotates, so the decoded frame has the swapped size
    return w, h, dur


def term_size():
    rows, cols, pw, ph = struct.unpack("HHHH", fcntl.ioctl(1, termios.TIOCGWINSZ, b"\0" * 8))
    if not pw or not ph: pw, ph = cols * 10, rows * 22
    return rows, cols, pw / cols, ph / rows


vw, vh, dur = probe()
if not vw or not vh:
    sys.exit(1)
rows, cols, cw, ch = term_size()
areaw, areah = cols * cw, (rows - 2) * ch  # last row = progress bar, first row = title
s = min(areaw / vw, areah / vh)
dispw, disph = vw * s, vh * s
ccols, crows = max(1, int(dispw / cw)), max(1, int(disph / ch))
d = min(1.0, (PIXEL_BUDGET / (dispw * disph)) ** 0.5)
W, H = max(2, int(dispw * d) // 2 * 2), max(2, int(disph * d) // 2 * 2)
x0, y0 = max(1, (cols - ccols) // 2 + 1), 2 + max(0, ((rows - 2) - crows) // 2)

out = sys.stdout.buffer


def send(frame):
    data = base64.standard_b64encode(zlib.compress(frame, 1))
    out.write(b"\x1b[%d;%dH" % (y0, x0))
    for i in range(0, len(data), 4096):
        more = 1 if i + 4096 < len(data) else 0
        head = (b"a=T,f=24,o=z,s=%d,v=%d,i=1,p=1,c=%d,r=%d,C=1,q=2,m=%d" % (W, H, ccols, crows, more)) if i == 0 \
            else b"m=%d" % more
        out.write(b"\x1b_G" + head + b";" + data[i:i + 4096] + b"\x1b\\")
    out.flush()


def fmt(t):
    t = int(max(0, t))
    return "%d:%02d" % (t // 60, t % 60)


fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
tty.setcbreak(fd)
ff = pl = None
base = 0.0
n = 0
start = 0.0
paused_at = None
done = False
size = W * H * 3


def pos():
    return base + max(0, n - 1) / FPS


def stop_procs():
    global ff, pl
    for p in (ff, pl):
        if p and p.poll() is None:
            p.send_signal(signal.SIGCONT); p.kill()
            p.wait()
    ff = pl = None


def launch(p):
    """(re)start decoding and sound at media position p seconds"""
    global ff, pl, base, n, start, paused_at, done
    stop_procs()
    if dur: p = min(p, max(0.0, dur - 0.5))
    p = max(0.0, p)
    ss = ["-ss", "%.2f" % p]
    pl = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"] + ss + [path],
                          stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "quiet"] + ss + ["-i", path, "-an", "-vf",
                          f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdin=DEVNULL, stdout=subprocess.PIPE)
    base, n, paused_at, done = p, 0, None, False
    start = time.time() + 0.2  # ffplay needs a moment to open the audio device


def toggle_pause():
    global paused_at, start
    if done: return
    if paused_at is None:
        paused_at = time.time(); pl.send_signal(signal.SIGSTOP)
    else:
        start += time.time() - paused_at; paused_at = None; pl.send_signal(signal.SIGCONT)


def bar(msg_extra=""):
    p = pos()
    left = " %s %s " % ("⏸" if paused_at is not None else ("■" if done else "▶"), fmt(p))
    right = " %s " % fmt(dur) if dur else " "
    hint = "  ←→ 5s  j/l 10s  space  q" if cols > 70 else ""
    w = max(4, cols - len(left) - len(right) - len(hint) - 1)
    f = min(w - 1, int(w * p / dur)) if dur else 0
    line = left + "━" * f + "●" + "─" * (w - 1 - f) + right + hint
    out.write(b"\x1b[%d;1H\x1b[2K%s" % (rows, line.encode()))
    out.flush()


def seek_to(t):
    launch(t)


MOUSE = re.compile(rb"\x1b\[<(\d+);(\d+);(\d+)([Mm])")
KEYS = {b"\x1b[D": -5, b"\x1b[C": 5, b"\x1b[1;2D": -10, b"\x1b[1;2C": 10, b"\x1b[B": -10, b"\x1b[A": 10,
        b"j": -10, b"l": 10, b"h": -5, b"k": 5}
click_t = None
last_bar = 0.0
quit_ = False


def handle(data):
    """returns True if the frame in hand is stale (a seek happened)"""
    global click_t, quit_
    stale = False
    for m in MOUSE.finditer(data):
        b, x, y, kind = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        if kind != b"M" or b != 0: continue
        if y == rows and dur:
            seek_to(dur * (x - 1) / max(1, cols - 1)); stale = True; click_t = None
        elif click_t is not None and time.time() - click_t[0] < 0.35:
            side = click_t[1]; click_t = None
            if side < cols / 3: seek_to(pos() - 10); stale = True
            elif side > cols * 2 / 3: seek_to(pos() + 10); stale = True
        else:
            click_t = (time.time(), x)
    delta = 0
    for k in re.findall(rb"\x1b\[1;2[CD]|\x1b\[[A-D]|.", MOUSE.sub(b"", data), re.S):  # repeated keys arrive glued
        if k in KEYS: delta += KEYS[k]
        elif k == b" ": toggle_pause()
        elif k in (b"o", b"O"):
            subprocess.Popen(["xdg-open", path], stdout=DEVNULL, stderr=DEVNULL)
            quit_ = True
        elif k in (b"q", b"Q", b"\x1b", b"\r", b"\n"): quit_ = True
        elif k.isdigit() and dur:
            seek_to(dur * int(k) / 10); stale = True
    if delta:
        seek_to(pos() + delta); stale = True
    return stale


try:
    out.write(b"\x1b[2J\x1b[H\x1b[?25l\x1b[?1000h\x1b[?1006h")
    name = os.path.basename(path)
    out.write(b"\x1b[1;2H\x1b[2m%s\x1b[0m" % name.encode())
    launch(0.0)
    while not quit_:
        buf = None
        if paused_at is None and not done:
            buf = ff.stdout.read(size)
            if len(buf) < size:
                done = True
                buf = None
            else:
                due = start + n / FPS
                n += 1
                wait = due - time.time()
                if wait < -1.0 / FPS:
                    buf = None  # late: drop the frame to stay in sync with the sound
                    if select.select([fd], [], [], 0)[0]: handle(os.read(fd, 64))
                    continue
                timeout = max(0, wait)
        else:
            timeout = 0.1
        if select.select([fd], [], [], timeout)[0]:
            if handle(os.read(fd, 64)): buf = None
        if click_t is not None and time.time() - click_t[0] >= 0.35:
            click_t = None; toggle_pause()  # single click = pause/resume
        if buf is not None and paused_at is None:
            send(buf)
        if time.time() - last_bar > 0.25:
            last_bar = time.time(); bar()
finally:
    stop_procs()
    out.write(b"\x1b[?1000l\x1b[?1006l\x1b_Ga=d,d=A,q=2\x1b\\\x1b[?25h")
    out.flush()
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
