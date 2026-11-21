#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Writes one invented passport spread to /output/entry.png (1024x1024 PNG,
stdlib only, no network, deterministic).

Country: the Republic of Auralia, an archipelago. Holder: Elena Vera Marlowe.
Every date is internally consistent: passport issued 14 MAR 2023, expires
14 MAR 2033; every stamp falls after the issue date and in chronological
order; the Norvane visa (11 SEP 2024 - 11 DEC 2024) brackets its entry and
exit stamps. The MRZ check digits are computed for real.
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (242, 236, 221)
PAPER_DK = (228, 220, 200)
INK = (30, 42, 56)
INK_MD = (58, 74, 92)
GOLD = (138, 109, 47)
GOLD_LT = (172, 143, 80)
BLUE = (43, 77, 143)
PURPLE = (107, 63, 143)
GREEN = (47, 107, 74)
TEAL = (47, 107, 107)
VISA_BG = (221, 231, 238)
PORTRAIT_BG = (174, 191, 204)
SKIN = (230, 189, 147)
SKIN_DK = (214, 168, 124)
HAIR = (74, 50, 38)
JACKET = (42, 58, 82)
LIGHT_LINE = (203, 192, 168)
FAINT = (224, 216, 192)

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows; each row is a 5-bit integer, bit 4 = leftmost pixel.
FONT = {
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    'D': [0b11100, 0b10010, 0b10001, 0b10001, 0b10001, 0b10010, 0b11100],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    'J': [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    '0': [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    '3': [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    '6': [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
    ' ': [0, 0, 0, 0, 0, 0, 0],
    '.': [0, 0, 0, 0, 0, 0b01100, 0b01100],
    ',': [0, 0, 0, 0, 0b01100, 0b00100, 0b01000],
    '-': [0, 0, 0, 0b01110, 0, 0, 0],
    '/': [0b00001, 0b00010, 0b00010, 0b00100, 0b00100, 0b01000, 0b01000],
    '<': [0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010],
    '>': [0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000],
    '(': [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ')': [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
    ':': [0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0],
    ';': [0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000],
    "'": [0b00100, 0b00100, 0b01000, 0, 0, 0, 0],
    '&': [0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101],
    '+': [0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0],
    '=': [0, 0, 0b11111, 0, 0b11111, 0, 0],
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100],
    '?': [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0, 0b00100],
    '"': [0b01010, 0b01010, 0, 0, 0, 0, 0],
    '*': [0, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0],
    '%': [0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011],
    '#': [0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010],
    '_': [0, 0, 0, 0, 0, 0, 0b11111],
    '[': [0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110],
    ']': [0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110],
}


def text_width(s, scale, advance=None):
    adv = advance if advance is not None else 6 * scale
    return len(s) * adv - (adv - 5 * scale) if s else 0


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.clip = None  # (x, y, w, h) or None
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if self.clip is not None:
            cx, cy, cw, ch = self.clip
            if not (cx <= x < cx + cw and cy <= y < cy + ch):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def set_clip(self, rect):
        self.clip = rect

    def clear_clip(self):
        self.clip = None

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if self.clip is not None:
            cx, cy, cw, ch = self.clip
            x0 = max(x0, cx)
            y0 = max(y0, cy)
            x1 = min(x1, cx + cw)
            y1 = min(y1, cy + ch)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        for k in range(t):
            self.fill_rect(x, y + k, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for k in range(t):
            self.fill_rect(x + k, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def rect_outline(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / ry
            if abs(dy) > 1:
                continue
            hw = int(rx * (1 - dy * dy) ** 0.5)
            self.fill_rect(cx - hw, yy, 2 * hw + 1, 1, c)

    def circle_outline(self, cx, cy, r, c, t=1):
        import math
        steps = max(48, r * 6)
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            for dx in range(t):
                for dy in range(t):
                    self.set(x + dx, y + dy, c)

    def text(self, s, x, y, scale, c, advance=None):
        adv = advance if advance is not None else 6 * scale
        cx = x
        for ch in s.upper():
            g = FONT.get(ch)
            if g is None:
                cx += adv
                continue
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += adv
        return cx

    def text_center(self, s, cx, y, scale, c, advance=None):
        w = text_width(s, scale, advance)
        return self.text(s, cx - w // 2, y, scale, c, advance)

    def wrap(self, s, x, y, max_w, scale, c, lh=None):
        adv = 6 * scale
        per = max(1, max_w // adv)
        words = s.split(' ')
        lines = []
        cur = ''
        for wd in words:
            trial = (cur + ' ' + wd).strip()
            if len(trial) <= per:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        yy = y
        step = lh if lh is not None else 9 * scale
        for ln in lines:
            self.text(ln, x, yy, scale, c)
            yy += step
        return yy


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3]
    png = b'\x89PNG\r\n\x1a\n'
    png += _chunk(b'IHDR', ihdr)
    png += _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += _chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- MRZ
_MRZ_VAL = {}
for _i, _ch in enumerate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    _MRZ_VAL[_ch] = _i
_MRZ_VAL['<'] = 0


def mrz_check(s):
    total = 0
    for i, ch in enumerate(s):
        total += _MRZ_VAL[ch] * (7, 3, 1)[i % 3]
    return str(total % 10)


def build_mrz():
    line1 = 'P<AURMARLOWE<<ELENA<VERA'
    line1 = line1 + '<' * (44 - len(line1))
    doc = 'AU4829176'
    dob = '940602'
    exp = '330314'
    personal = '<' * 14
    body = (doc + mrz_check(doc) + 'AUR' + dob + mrz_check(dob) + 'F'
            + exp + mrz_check(exp) + personal + mrz_check(personal))
    line2 = body + mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


# ---------------------------------------------------------------- rotated stamps
class Layer:
    """Small offscreen drawing surface with a transparency mask."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.mask = bytearray(w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c
            self.mask[y * self.w + x] = 1

    def fill_rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        for k in range(t):
            self.fill_rect(x, y + k, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for k in range(t):
            self.fill_rect(x + k, y, 1, h, c)

    def rect_outline(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / ry
            if abs(dy) > 1:
                continue
            hw = int(rx * (1 - dy * dy) ** 0.5)
            self.fill_rect(cx - hw, yy, 2 * hw + 1, 1, c)

    def circle_outline(self, cx, cy, r, c, t=1):
        import math
        steps = max(48, r * 6)
        for k in range(steps):
            a = 2 * math.pi * k / steps
            self.set(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)

    def ellipse_outline(self, cx, cy, rx, ry, c, t=1):
        import math
        steps = max(64, (rx + ry) * 3)
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = int(cx + rx * math.cos(a))
            y = int(cy + ry * math.sin(a))
            for dx in range(t):
                for dy in range(t):
                    self.set(x + dx, y + dy, c)

    def text(self, s, x, y, scale, c, advance=None):
        adv = advance if advance is not None else 6 * scale
        cx = x
        for ch in s.upper():
            g = FONT.get(ch)
            if g is None:
                cx += adv
                continue
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += adv
        return cx

    def text_center(self, s, cx, y, scale, c, advance=None):
        w = text_width(s, scale, advance)
        return self.text(s, cx - w // 2, y, scale, c, advance)


def blit_rotated(cv, layer, cx, cy, angle_deg):
    import math
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    r = int((max(layer.w, layer.h) * 0.75)) + 2
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            # dest -> source (rotate back by the angle)
            sx = int(layer.w // 2 + dx * ca + dy * sa)
            sy = int(layer.h // 2 - dx * sa + dy * ca)
            if 0 <= sx < layer.w and 0 <= sy < layer.h:
                if layer.mask[sy * layer.w + sx]:
                    i = (sy * layer.w + sx) * 3
                    cv.set(cx + dx, cy + dy,
                           (layer.px[i], layer.px[i + 1], layer.px[i + 2]))


def stamp_rect(w, h, color, lines, scale=2):
    """Rectangular entry/exit stamp. lines = list of (text, scale)."""
    lay = Layer(w, h)
    lay.rect_outline(3, 3, w - 6, h - 6, color, 3)
    lay.rect_outline(9, 9, w - 18, h - 18, color, 1)
    y = 16
    for txt, sc in lines:
        lay.text_center(txt, w // 2, y, sc, color)
        y += 9 * sc + 4
    return lay


def stamp_oval(w, h, color, lines, scale=2):
    lay2 = Layer(w, h)
    lay2.ellipse_outline(w // 2, h // 2, w // 2 - 4, h // 2 - 4, color, 3)
    lay2.ellipse_outline(w // 2, h // 2, w // 2 - 13, h // 2 - 13, color, 1)
    y = h // 2 - (len(lines) * (9 * scale + 4)) // 2
    for txt, sc in lines:
        lay2.text_center(txt, w // 2, y, sc, color)
        y += 9 * sc + 4
    return lay2


# ---------------------------------------------------------------- emblem
def draw_emblem(cv, cx, cy, r, c):
    import math
    cv.circle_outline(cx, cy, r, c, 2)
    cv.circle_outline(cx, cy, r - 5, c, 1)
    for k in range(8):
        a = math.pi * k / 4
        x2 = int(cx + (r - 6) * math.cos(a))
        y2 = int(cy + (r - 6) * math.sin(a))
        cv.line(cx, cy, x2, y2, c)
    cv.ellipse(cx, cy, 5, 5, c)
    cv.text_center('AU', cx, cy - 26, 1, c)


# ---------------------------------------------------------------- portrait
def draw_portrait(cv, x, y, w, h):
    cv.set_clip((x, y, w, h))
    cv.fill_rect(x, y, w, h, PORTRAIT_BG)
    # shoulders / jacket
    cv.ellipse(x + w // 2, y + h + 18, w // 2 + 6, 52, JACKET)
    cv.fill_rect(x, y + h - 42, w, 42, JACKET)
    # shirt V
    cv.line(x + w // 2 - 16, y + h - 42, x + w // 2, y + h - 18, (240, 240, 235))
    cv.line(x + w // 2 + 16, y + h - 42, x + w // 2, y + h - 18, (240, 240, 235))
    # neck
    cv.fill_rect(x + w // 2 - 13, y + h - 78, 26, 40, SKIN_DK)
    # head
    cx = x + w // 2
    cv.ellipse(cx, y + 78, 40, 50, SKIN)
    # ears
    cv.ellipse(cx - 40, y + 80, 6, 10, SKIN)
    cv.ellipse(cx + 40, y + 80, 6, 10, SKIN)
    # hair: cap + side sweeps
    cv.ellipse(cx, y + 44, 42, 26, HAIR)
    cv.fill_rect(cx - 42, y + 40, 14, 46, HAIR)
    cv.fill_rect(cx + 28, y + 40, 14, 46, HAIR)
    cv.ellipse(cx, y + 62, 40, 12, SKIN)  # forehead line
    # brows
    cv.fill_rect(cx - 26, y + 66, 18, 3, HAIR)
    cv.fill_rect(cx + 8, y + 66, 18, 3, HAIR)
    # eyes
    cv.ellipse(cx - 17, y + 76, 5, 3, INK)
    cv.ellipse(cx + 17, y + 76, 5, 3, INK)
    # nose
    cv.line(cx, y + 80, cx - 2, y + 96, SKIN_DK)
    cv.line(cx - 2, y + 96, cx + 3, y + 96, SKIN_DK)
    # mouth
    cv.line(cx - 12, y + 110, cx + 12, y + 110, (150, 90, 80))
    cv.line(cx - 12, y + 110, cx - 8, y + 108, (150, 90, 80))
    cv.line(cx + 12, y + 110, cx + 8, y + 108, (150, 90, 80))
    # small corner stamp overlapping the photo
    cv.circle_outline(x + w - 26, y + h - 26, 20, GOLD, 2)
    cv.text_center('AU', x + w - 26, y + h - 30, 1, GOLD)
    cv.clear_clip()


# ---------------------------------------------------------------- pages
def draw_left_page(cv):
    # frame
    cv.rect_outline(28, 28, 472, 968, GOLD, 2)
    cv.rect_outline(34, 34, 460, 956, LIGHT_LINE, 1)
    # emblem + header
    draw_emblem(cv, 264, 96, 30, GOLD)
    cv.text_center('REPUBLIC OF AURALIA', 264, 140, 3, INK)
    cv.text_center('PASSPORT', 264, 172, 4, INK)
    cv.hline(60, 210, 408, GOLD, 2)
    cv.text('DATA PAGE', 48, 224, 1, INK_MD)
    cv.text('NO. AU 482 917 6', 330, 224, 1, INK_MD)
    # portrait
    cv.rect_outline(46, 248, 164, 204, INK, 2)
    draw_portrait(cv, 50, 252, 156, 196)
    # data fields
    fields = [
        ('SURNAME', 'MARLOWE'),
        ('GIVEN NAMES', 'ELENA VERA'),
        ('NATIONALITY', 'AURALIAN'),
        ('DATE OF BIRTH', '02 JUN 1994'),
        ('PLACE OF BIRTH', 'PORT MERIDIAN'),
        ('SEX', 'F'),
        ('DATE OF ISSUE', '14 MAR 2023'),
        ('DATE OF EXPIRY', '14 MAR 2033'),
        ('AUTHORITY', 'MINISTRY OF INTERIOR'),
    ]
    fy = 252
    for label, value in fields:
        cv.text(label, 230, fy, 1, INK_MD)
        cv.text(value, 230, fy + 10, 2, INK)
        fy += 32
    # signature under portrait
    cv.text("HOLDER'S SIGNATURE", 48, 466, 1, INK_MD)
    import math
    for xx in range(48, 206):
        yy = 492 + int(4 * math.sin((xx - 48) / 9.0)) + (3 if xx % 23 < 3 else 0)
        cv.set(xx, yy, INK)
        cv.set(xx, yy + 1, INK)
    cv.hline(48, 502, 160, INK_MD, 1)
    cv.text('ELENA MARLOWE', 48, 510, 1, INK)
    # MRZ band
    cv.fill_rect(40, 560, 448, 66, (233, 226, 205))
    cv.rect_outline(40, 560, 448, 66, LIGHT_LINE, 1)
    m1, m2 = build_mrz()
    cv.text(m1, 48, 572, 1, INK, advance=10)
    cv.text(m2, 48, 594, 1, INK, advance=10)
    # guilloche waves, lower area
    for band in range(660, 940, 34):
        for xx in range(40, 488, 4):
            yy = band + int(5 * math.sin(xx / 26.0))
            cv.set(xx, yy, FAINT)
            cv.set(xx, yy + 1, FAINT)
    cv.text_center('PROPERTY OF THE REPUBLIC OF AURALIA', 264, 962, 1, INK_MD)


def draw_right_page(cv):
    cv.rect_outline(524, 28, 472, 968, GOLD, 2)
    cv.rect_outline(530, 34, 460, 956, LIGHT_LINE, 1)
    cv.text_center('VISAS AND STAMPS', 760, 48, 3, INK)
    cv.hline(556, 84, 408, GOLD, 2)
    # visa sticker
    cv.fill_rect(548, 100, 424, 138, VISA_BG)
    cv.rect_outline(548, 100, 424, 138, BLUE, 2)
    cv.rect_outline(554, 106, 412, 126, BLUE, 1)
    cv.text_center('KINGDOM OF NORVANE', 760, 116, 2, BLUE)
    cv.text_center('VISITOR VISA', 760, 136, 2, BLUE)
    cv.hline(566, 160, 388, BLUE, 1)
    cv.text('VALID FROM 11 SEP 2024', 566, 172, 1, INK)
    cv.text('VALID UNTIL 11 DEC 2024', 566, 188, 1, INK)
    cv.text('ENTRIES: SINGLE', 566, 204, 1, INK)
    cv.text('VISA NO. VN-2024-11873', 566, 220, 1, INK)
    cv.text('FEE PAID 40 NOR', 820, 204, 1, INK)
    # stamps, two columns, chronological top to bottom
    s1 = stamp_oval(196, 96, BLUE,
                    [('THALASSIA', 2), ('ENTRY', 2), ('22 JUN 2023', 2)])
    blit_rotated(cv, s1, 652, 300, -8)
    s2 = stamp_oval(196, 96, BLUE,
                    [('THALASSIA', 2), ('EXIT', 2), ('30 JUN 2023', 2)])
    blit_rotated(cv, s2, 868, 300, 7)
    s3 = stamp_rect(196, 96, PURPLE,
                    [('NORVANE', 2), ('ENTRY', 2), ('11 SEP 2024', 2)])
    blit_rotated(cv, s3, 652, 420, -6)
    s4 = stamp_rect(196, 96, PURPLE,
                    [('NORVANE', 2), ('EXIT', 2), ('28 OCT 2024', 2)])
    blit_rotated(cv, s4, 868, 420, 8)
    s5 = stamp_oval(196, 96, GREEN,
                    [('CALDORRA', 2), ('ENTRY', 2), ('05 MAY 2025', 2)])
    blit_rotated(cv, s5, 652, 540, -7)
    s6 = stamp_oval(196, 96, GREEN,
                    [('CALDORRA', 2), ('EXIT', 2), ('19 MAY 2025', 2)])
    blit_rotated(cv, s6, 868, 540, 6)
    # tide-fee circular stamp
    fee = Layer(150, 150)
    fee.circle_outline(75, 75, 70, TEAL, 3)
    fee.circle_outline(75, 75, 58, TEAL, 1)
    fee.text_center('TIDE FEE', 75, 48, 2, TEAL)
    fee.text_center('PAID', 75, 68, 2, TEAL)
    fee.text_center('12 AUR', 75, 92, 2, TEAL)
    blit_rotated(cv, fee, 650, 680, -12)
    # condition of stay box
    cv.fill_rect(548, 780, 424, 118, (238, 232, 214))
    cv.rect_outline(548, 780, 424, 118, INK_MD, 2)
    cv.text_center('CONDITION OF STAY', 760, 792, 2, INK)
    cv.hline(566, 816, 388, INK_MD, 1)
    cv.wrap('THE HOLDER MAY NOT ENTER THE NORTHERN REEF ZONE WITHOUT A TIDE '
            'PERMIT. - MINISTRY OF THE INTERIOR', 566, 828, 388, 1, INK)
    # footer note
    cv.wrap('ARRIVAL AND DEPARTURE STAMPS MUST AGREE WITH THE VISA ABOVE. '
            'ISSUED AT PORT MERIDIAN.', 548, 924, 424, 1, INK_MD)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    # centre gutter
    cv.vline(511, 28, 968, GOLD, 2)
    draw_left_page(cv)
    draw_right_page(cv)
    path = os.path.join(out_dir, 'entry.png')
    n = write_png(cv, path)
    print('wrote', path, n, 'bytes,', W, 'x', H)
    assert n <= 1048576, 'too big'
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
