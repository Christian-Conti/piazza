#!/usr/bin/env python3
"""In-terminal video player for kitty: ffmpeg decodes, frames go over the kitty graphics protocol, ffplay plays the
sound. Starts at once (no conversion step). Keys: space pause/resume, o open in system player, any other key quits."""
import base64, fcntl, os, select, signal, struct, subprocess, sys, termios, time, tty, zlib

FPS = 12
path = sys.argv[1]


def probe():
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:stream_tags=rotate", "-of", "default=nw=1",
                          path], capture_output=True, text=True).stdout
    w = h = rot = 0
    for line in out.splitlines():
        k, _, v = line.partition("=")
        if k == "width": w = int(v)
        elif k == "height": h = int(v)
        elif k in ("rotation", "rotate"):
            try: rot = int(float(v))
            except ValueError: pass
    if abs(rot) % 180 == 90: w, h = h, w  # ffmpeg autorotates, so the decoded frame has the swapped size
    return w, h


def term_size():
    rows, cols, pw, ph = struct.unpack("HHHH", fcntl.ioctl(1, termios.TIOCGWINSZ, b"\0" * 8))
    if not pw or not ph: pw, ph = cols * 10, rows * 22
    return rows, cols, pw // cols, ph // rows


vw, vh = probe()
if not vw or not vh:
    sys.exit(1)
rows, cols, cw, ch = term_size()
maxw = min(640, (cols - 2) * cw)
maxh = min(480, (rows - 4) * ch)
s = min(maxw / vw, maxh / vh, 1.0)
W, H = max(2, int(vw * s) // 2 * 2), max(2, int(vh * s) // 2 * 2)
ccols, crows = max(1, round(W / cw)), max(1, round(H / ch))
x0, y0 = max(1, (cols - ccols) // 2 + 1), 2

out = sys.stdout.buffer


def send(frame):
    data = base64.standard_b64encode(zlib.compress(frame, 1))
    out.write(b"\x1b[%d;%dH" % (y0, x0))
    first = True
    for i in range(0, len(data), 4096):
        chunk = data[i:i + 4096]
        more = 1 if i + 4096 < len(data) else 0
        head = (b"a=T,f=24,o=z,s=%d,v=%d,i=1,p=1,c=%d,r=%d,C=1,q=2,m=%d" % (W, H, ccols, crows, more)) if first \
            else b"m=%d" % more
        out.write(b"\x1b_G" + head + b";" + chunk + b"\x1b\\")
        first = False
    out.flush()


def status(msg):
    out.write(b"\x1b[%d;1H\x1b[2K  %s" % (y0 + crows + 1, msg.encode()))
    out.flush()


fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
tty.setcbreak(fd)
ff = pl = None
try:
    out.write(b"\x1b[2J\x1b[H\x1b[?25l")
    name = os.path.basename(path)
    status(f"{name}  -  space pause · o open in player · any other key close")
    pl = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i", path, "-an", "-vf", f"fps={FPS},scale={W}:{H}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE)
    size = W * H * 3
    start = time.time() + 0.2  # ffplay needs a moment to open the audio device
    n = 0
    paused_at = None
    done = False
    while True:
        if paused_at is None and not done:
            buf = ff.stdout.read(size)
            if len(buf) < size:
                done = True
                status(f"{name}  -  finished · any key to close")
                continue
            due = start + n / FPS
            n += 1
            wait = due - time.time()
            if wait < -1.0 / FPS:
                continue  # late: drop the frame to stay in sync with the sound
            timeout = max(0, wait)
            first_frame = buf
        else:
            timeout = 0.1
        r, _, _ = select.select([fd], [], [], timeout)
        if r:
            k = os.read(fd, 8)
            if k == b" " and not done:
                if paused_at is None:
                    paused_at = time.time(); pl.send_signal(signal.SIGSTOP)
                else:
                    start += time.time() - paused_at; paused_at = None; pl.send_signal(signal.SIGCONT)
                continue
            if k in (b"o", b"O"):
                subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        if paused_at is None and not done:
            send(buf)
finally:
    for p in (ff, pl):
        if p and p.poll() is None:
            p.send_signal(signal.SIGCONT); p.kill()
    out.write(b"\x1b_Ga=d,d=A,q=2\x1b\\\x1b[?25h")
    out.flush()
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
