"""Front-page renderer for the 27 November 2026 world-news image.

Pure Python 3.13 stdlib. Own framebuffer, own bitmap-font text, own PNG
encoder (zlib + hand-built chunks). No network, no clock, no randomness:
the same code always draws the same bytes.
"""
import base64
import binascii
import math
import struct
import zlib

from fontdata import FONTS

W = 1024
H = 1024
PAPER = (255, 255, 255)
INK = (18, 18, 18)
RED = (148, 18, 18)
GREY = (120, 118, 112)
PANEL = (246, 244, 239)
LIGHT = (232, 230, 224)

MX = 36            # left / right margin
CX = W - MX        # content right edge
CW = CX - MX       # content width


# ---------------------------------------------------------------- fonts
class Font:
    def __init__(self, blob_b64):
        raw = base64.b64decode(blob_b64)
        self.ascent, count = struct.unpack_from(">HH", raw, 0)
        off = 4
        self.glyphs = {}
        for _ in range(count):
            code, adv, left, top, w, h = struct.unpack_from(">HBbbBB", raw, off)
            off += 7
            nbytes = (w * h + 7) // 8
            bits = raw[off:off + nbytes]
            off += nbytes
            self.glyphs[code] = (adv, left, top, w, h, bits)

    def width(self, text):
        total = 0
        for ch in text:
            g = self.glyphs.get(ord(ch))
            total += g[0] if g else self.glyphs[ord("?")][0]
        return total

    def line_height(self):
        return self.ascent + 8


_FONTS = {}


def font(name):
    if name not in _FONTS:
        _FONTS[name] = Font(FONTS[name])
    return _FONTS[name]


def wrap(text, fname, width):
    """Greedy word wrap; returns a list of lines, each fitting `width`."""
    f = font(fname)
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if f.width(trial) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self):
        self.buf = bytearray([255]) * (W * H * 3)

    def px(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(H, y1)):
            i = (y * W + max(0, x0)) * 3
            j = (y * W + min(W, x1)) * 3
            self.buf[i:j] = bytes(color) * ((j - i) // 3)

    def hline(self, x0, x1, y, color, thick=1):
        self.rect(x0, y, x1, y + thick, color)

    def vline(self, x, y0, y1, color, thick=1):
        self.rect(x, y0, x + thick, y1, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(thick):
                for b in range(thick):
                    self.px(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px(x, y, color)

    def ring(self, cx, cy, r, color, thick=2):
        for y in range(cy - r - 1, cy + r + 2):
            for x in range(cx - r - 1, cx + r + 2):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if abs(d - r) <= thick / 2:
                    self.px(x, y, color)

    def text(self, x, y_base, fname, s, color):
        f = font(fname)
        cx = x
        for ch in s:
            g = f.glyphs.get(ord(ch))
            if g is None:
                g = f.glyphs[ord("?")]
            adv, left, top, w, h, bits = g
            if w and h:
                bit = 0
                for yy in range(h):
                    for xx in range(w):
                        byte = bits[bit // 8]
                        on = (byte >> (7 - bit % 8)) & 1
                        bit += 1
                        if on:
                            self.px(cx + left + xx, y_base + top + yy, color)
            cx += adv
        return cx

    def text_centred(self, cx, y_base, fname, s, color):
        self.text(cx - font(fname).width(s) // 2, y_base, fname, s, color)

    def para(self, x, y_base, fname, text, width, color, lh=None):
        f = font(fname)
        lh = lh or f.line_height()
        y = y_base
        for ln in wrap(text, fname, width):
            self.text(x, y, fname, ln, color)
            y += lh
        return y


# ---------------------------------------------------------------- pictogram
def draw_drone(cv, x0, y0, x1, y1):
    """A quadcopter drone over a burst, drawn procedurally in the box."""
    cx = (x0 + x1) // 2 - 30
    cy = (y0 + y1) // 2 - 12
    # dashed flight path
    for i in range(0, 120, 14):
        cv.rect(x0 + 6 + i, cy - 46, x0 + 16 + i, cy - 44, GREY)
    # rotor arms
    for (ax, ay) in ((cx - 52, cy - 34), (cx + 52, cy - 34),
                     (cx - 52, cy + 30), (cx + 52, cy + 30)):
        cv.line(cx, cy, ax, ay, INK, 4)
        cv.disc(ax, ay, 7, INK)
        cv.hline(ax - 30, ax + 30, ay - 3, INK, 3)
    # body
    cv.rect(cx - 34, cy - 14, cx + 34, cy + 14, INK)
    cv.rect(cx - 20, cy - 6, cx + 20, cy + 6, RED)
    cv.disc(cx, cy + 22, 6, INK)
    # explosion burst, lower right
    bx, by = x1 - 62, y1 - 34
    for k in range(12):
        a = k * math.pi / 6
        r1, r2 = 12, 34 if k % 2 == 0 else 20
        cv.line(bx + int(r1 * math.cos(a)), by + int(r1 * math.sin(a)),
                bx + int(r2 * math.cos(a)), by + int(r2 * math.sin(a)), RED, 3)
    cv.disc(bx, by, 12, RED)
    cv.disc(bx, by, 5, PAPER)


# ---------------------------------------------------------------- content
MASTHEAD = "THE WORLD TODAY"
DATE_LINE = "FRIDAY, 27 NOVEMBER 2026"

LEAD_KICKER = "LEAD STORY  •  MIDDLE EAST"
LEAD_HEAD = ["IRANIAN DRONES HIT KUWAIT;",
             "TWO ITALIAN WORKERS KILLED"]
LEAD_DECK = (
    "Kuwait says Iranian drones struck a site in the country, killing two "
    "Italian workers. Tehran denies any role in the attack, as the region "
    "braces for what comes next."
)

PANELS = [
    ("WEATHER  •  UNITED STATES",
     "U.S. THANKSGIVING\nSTORM",
     "The 100th Macy's Thanksgiving Day Parade in New York was delayed for "
     "the first time as a storm swept the country. More than 600,000 "
     "homes and businesses lost power, hundreds of flights were cancelled, "
     "and about 80 million people were travelling."),
    ("ENERGY  •  SAUDI ARABIA",
     "STRIKE ON SAUDI\nREFINERY",
     "An enemy projectile hit the Jazan refinery in Saudi Arabia, setting "
     "it ablaze. One Nepalese worker was killed and several were hurt. The "
     "Saudi-led coalition said it intercepted Houthi drones near the port "
     "of Jeddah."),
    ("CONFLICT  •  GAZA",
     "GAZA: HAMAS\nOFFICIAL KILLED",
     "An Israeli strike in Gaza killed a senior Hamas official, his wife "
     "and his children. Ten people were killed in Gaza in all. Hamas said "
     "it was considering its response."),
]

STRIP_KICKER = "WORLD CHESS CHAMPIONSHIP  •  GAME 3"
STRIP_TEXT = (
    "Gukesh vs Sindarov ends in a marathon draw after 43 moves — "
    "still level after three games."
)

BRIEFS = [
    "Egypt held a driver over a Cairo tanker-truck fire that killed 31 people.",
    "Kim Jong Un toured a nuclear site and urged wider use of tactical nuclear arms.",
    "Gérard Depardieu will stand trial over an alleged 2018 rape.",
    "Trump demanded a probe into U.S. GDP figures he called fake, after growth was revised to 4.3%.",
    "Elon Musk said every child in America will get two shares of SpaceX.",
    "A Bangkok oil-refinery blast hurt at least 9 people.",
    "The Ebola outbreak in Congo passed 12,000 cases.",
]

FOOTER = ("THE WORLD TODAY  •  FRIDAY, 27 NOVEMBER 2026  •  "
          "ALL STORIES FIRST REPORTED ON 27 NOVEMBER 2026")


def render():
    cv = Canvas()
    # ---- masthead
    cv.text_centred(W // 2, 88, "MASTHEAD", MASTHEAD, INK)
    cv.hline(MX, CX, 102, RED, 4)
    cv.text(MX, 128, "LABEL", "VOL. I — NO. 331", GREY)
    cv.text_centred(W // 2, 128, "DATE", DATE_LINE, INK)
    rw = font("LABEL").width("PRICE: FREE")
    cv.text(CX - rw, 128, "LABEL", "PRICE: FREE", GREY)
    cv.hline(MX, CX, 140, INK, 3)

    # ---- lead story
    cv.text(MX, 168, "LABEL", LEAD_KICKER, RED)
    y = 210
    for ln in LEAD_HEAD:
        assert font("HEADLINE").width(ln) <= CW, ln
        cv.text(MX, y, "HEADLINE", ln, INK)
        y += 46
    deck_w = 596
    cv.para(MX, 292, "DECK", LEAD_DECK, deck_w, INK, lh=25)
    draw_drone(cv, 664, 268, 988, 396)
    cv.hline(MX, CX, 408, INK, 2)

    # ---- three panels
    pw, gap = 304, 20
    py = 418
    for i, (kicker, head, body) in enumerate(PANELS):
        px0 = MX + i * (pw + gap)
        cv.rect(px0, py, px0 + pw, py + 262, PANEL)
        cv.hline(px0, px0 + pw, py, INK, 2)
        cv.hline(px0, px0 + pw, py + 260, INK, 2)
        cv.vline(px0, py, py + 262, INK, 2)
        cv.vline(px0 + pw - 2, py, py + 262, INK, 2)
        cv.text(px0 + 14, py + 20, "LABEL", kicker, RED)
        hy = py + 46
        for ln in head.split("\n"):
            assert font("PANELHEAD").width(ln) <= pw - 28, ln
            cv.text(px0 + 14, hy, "PANELHEAD", ln, INK)
            hy += 26
        cv.hline(px0 + 14, px0 + pw - 14, hy + 2, LIGHT, 2)
        end = cv.para(px0 + 14, hy + 22, "BODY", body, pw - 28, INK, lh=19)
        # para() returns the cursor past the last line; the last baseline
        # is one line-height above it and must stay inside the panel.
        assert end - 19 <= py + 254, (kicker, end - py)

    # ---- chess strip
    sy = 692
    cv.rect(MX, sy, CX, sy + 64, PANEL)
    cv.rect(MX, sy, MX + 8, sy + 64, RED)
    cv.text(MX + 24, sy + 22, "LABEL", STRIP_KICKER, RED)
    cv.para(MX + 24, sy + 48, "DECK", STRIP_TEXT, CW - 48, INK, lh=25)

    # ---- in brief
    by = 772
    cv.text(MX, by, "LABEL", "IN BRIEF", RED)
    cv.hline(MX, CX, by + 8, INK, 2)
    col_w = 466
    for col, items in enumerate((BRIEFS[:4], BRIEFS[4:])):
        bx = MX + col * (col_w + 20)
        iy = by + 32
        for item in items:
            lines = wrap("•  " + item, "BODY", col_w)
            assert len(lines) <= 2, item
            for ln in lines:
                cv.text(bx, iy, "BODY", ln, INK)
                iy += 19
            iy += 6

    # ---- footer
    cv.hline(MX, CX, 984, INK, 2)
    cv.text_centred(W // 2, 1008, "LABEL", FOOTER, INK)
    return cv


# ---------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def render_png():
    return encode_png(render())
