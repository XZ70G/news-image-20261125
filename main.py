#!/usr/bin/env python3
"""news-image-20261125 entry.

Draws a one-page newspaper front page summing up the world news of
Wednesday 25 November 2026, using only the Python standard library.
Writes one deterministic PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png). No network access.

The image is drawn pixel by pixel with a 5x7 bitmap font, so the
program is fully self-contained and its output bytes are identical
on every run. Layout: masthead, one lead story, four stories in a
2x2 grid, one wide story, and a news ticker.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 227)
INK = (26, 26, 26)
GREEN = (14, 59, 46)
RED = (179, 38, 30)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
MUTED = (85, 85, 85)
LIGHT = (232, 226, 208)
PANEL = (255, 255, 255)

# 5x7 bitmap font, uppercase only. Each glyph is seven rows of five
# characters; '#' is a filled pixel.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


class Canvas:
    """A simple RGB raster canvas."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thick) ** 2 <= d <= r * r:
                    self.set(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts

        def edge_x(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])

        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = edge_x(y, (ax, ay), (bx, by)), edge_x(y, (ax, ay), (cx, cy))
            else:
                xa, xb = edge_x(y, (bx, by), (cx, cy)), edge_x(y, (ax, ay), (cx, cy))
            lo, hi = sorted([int(xa), int(xb)])
            for x in range(lo, hi + 1):
                self.set(x, y, color)

    def text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, y, s, scale, color):
        w = self.text_width(s, scale)
        self.text((self.w - w) // 2, y, s, scale, color)

    def wrap(self, s, scale, max_w):
        """Wrap text to lines that fit max_w pixels; returns line list."""
        words = s.upper().split()
        lines = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if self.text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def to_png(self):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter: none
            start = y * self.w * 3
            raw += self.px[start:start + self.w * 3]

        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            return out

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        return png

# Six stories, all first reported on 25 November 2026.
LEAD = {
    "kicker": "CYBERATTACK",
    "icon": "shield",
    "headline": "CIA AND U.S. SPY CHIEF'S OFFICE HIT BY CYBERATTACK",
    "body": "CNN reported the CIA and the Director of National Intelligence were hit by a cyberattack. An open-source analysis system was affected, in the latest breach to hit U.S. intelligence.",
    "place": "WASHINGTON, U.S.",
}

GRID = [
    {
        "kicker": "TECH",
        "icon": "chip",
        "headline": "HUAWEI FOUND GUILTY OF STEALING U.S. TRADE SECRETS",
        "body": "A New York jury convicted Huawei on 10 of 12 counts after a three-month trial.",
        "place": "NEW YORK, U.S.",
    },
    {
        "kicker": "UKRAINE WAR",
        "icon": "ship",
        "headline": "RUSSIA CALLS UKRAINE SHIP STRIKES 'TERRORISM'",
        "body": "Moscow accused Kyiv of terrorism after drone strikes hit Russian ships in the Baltic and Libya.",
        "place": "MOSCOW / BENGHAZI",
    },
    {
        "kicker": "CONGO",
        "icon": "cross",
        "headline": "WHO PULLS STAFF FROM EBOLA HOSPITAL AS FIGHTING RAGES",
        "body": "WHO staff left an Ituri hospital after sheltering three days. Ebola has killed 5,775 people.",
        "place": "ITURI, DR CONGO",
    },
    {
        "kicker": "U.S.",
        "icon": "star",
        "headline": "TRUMP GIVES GIULIANI THE MEDAL OF FREEDOM",
        "body": "Trump gave the former New York mayor the Medal of Freedom, the highest U.S. civilian honour.",
        "place": "WASHINGTON, U.S.",
    },
]

WIDE = {
    "kicker": "MIDDLE EAST",
    "icon": "flame",
    "headline": "HOUTHI DRONE HITS RIYADH TOWER, 11 HURT",
    "body": "Saudi civil defence said eleven people were injured when a Houthi drone struck a tower in Riyadh.",
    "place": "RIYADH, SAUDI ARABIA",
}

TICKER = [
    "ALSO TODAY: TWO HELD AFTER BREAK-IN AT PRINCE WILLIAM'S HOME",
    "TRUMP TO UNVEIL NEW TARIFFS - GAZA TOLL 74,746 - 266M FACE HUNGER, WFP SAYS",
]


def draw_icon(cv, kind, x, y, size, color):
    """Draw a simple pictogram inside the square (x, y, size)."""
    cx, cy = x + size // 2, y + size // 2
    if kind == "shield":
        cv.triangle(cx, y + 4, x + 6, y + 20, x + size - 6, y + 20, color)
        cv.rect(x + 6, y + 20, size - 12, size // 2, color)
        cv.triangle(x + 6, y + 20 + size // 2, x + size - 6,
                    y + 20 + size // 2, cx, y + size - 4, color)
        cv.rect(cx - 5, cy - 12, 10, 26, PAPER)
        cv.rect(cx - 12, cy - 4, 24, 8, PAPER)
    elif kind == "chip":
        cv.rect(cx - 22, cy - 22, 44, 44, color)
        cv.rect(cx - 12, cy - 12, 24, 24, PAPER)
        cv.rect(cx - 5, cy - 5, 10, 10, color)
        for dx in (-18, 0, 18):
            cv.rect(cx + dx - 3, y + 2, 6, 12, color)
            cv.rect(cx + dx - 3, y + size - 14, 6, 12, color)
            cv.rect(x + 2, cy + dx - 3, 12, 6, color)
            cv.rect(x + size - 14, cy + dx - 3, 12, 6, color)
    elif kind == "ship":
        cv.rect(x + 8, cy + 6, size - 16, 14, color)
        cv.triangle(x + 8, cy + 6, x + size - 8, cy + 6, cx, cy + 26, color)
        cv.vline(cx, y + 8, 34, color)
        cv.triangle(cx, y + 8, cx, y + 30, cx + 26, y + 30, color)
        cv.hline(x, cy + 34, size, color)
        cv.hline(x + 10, cy + 42, size - 20, color)
    elif kind == "cross":
        cv.ring(cx, cy, size // 2 - 4, color, 4)
        cv.rect(cx - 6, cy - 20, 12, 40, color)
        cv.rect(cx - 20, cy - 6, 40, 12, color)
    elif kind == "star":
        for k in range(5):
            a = -math.pi / 2 + k * 2 * math.pi / 5
            b = a + math.pi / 5
            x0 = int(cx + 34 * math.cos(a))
            y0 = int(cy + 34 * math.sin(a))
            x1 = int(cx + 14 * math.cos(b))
            y1 = int(cy + 14 * math.sin(b))
            x2 = int(cx + 34 * math.cos(a + 2 * math.pi / 5))
            y2 = int(cy + 34 * math.sin(a + 2 * math.pi / 5))
            cv.triangle(cx, cy, x0, y0, x1, y1, color)
            cv.triangle(cx, cy, x1, y1, x2, y2, color)
    elif kind == "flame":
        cv.triangle(cx, y + 4, cx - 22, cy + 10, cx + 6, cy + 10, color)
        cv.triangle(cx + 6, cy - 6, cx - 16, cy + 30, cx + 24, cy + 30, color)
        cv.rect(cx - 16, cy + 30, 40, 8, color)
        cv.rect(cx - 26, cy + 44, 60, 6, color)


def draw_panel(cv, x, y, w, h, story, idx):
    cv.rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, 3, RED if idx % 2 == 0 else GREEN)
    cv.hline(x, y + h - 1, w, LIGHT)
    cv.vline(x + w - 1, y, h, LIGHT)
    cv.text(x + 14, y + 14, story["kicker"], 2, RED)
    ix, iy, isize = x + 14, y + 44, 56
    cv.rect(ix - 4, iy - 4, isize + 8, isize + 8, LIGHT)
    draw_icon(cv, story["icon"], ix, iy, isize, GREEN)
    tx = x + 92
    tw = w - 92 - 14
    lines = cv.wrap(story["headline"], 3, tw)[:3]
    ty = y + 46
    for line in lines:
        cv.text(tx, ty, line, 3, INK)
        ty += 22
    body_lines = cv.wrap(story["body"], 2, tw)[:3]
    ty += 4
    for line in body_lines:
        cv.text(tx, ty, line, 2, MUTED)
        ty += 15
    cv.hline(x + 14, y + h - 30, w - 28, LIGHT)
    cv.text(x + 14, y + h - 22, story.get("place", ""), 2, RED)


def build():
    cv = Canvas(W, H, PAPER)
    # Outer frame.
    cv.rect(0, 0, W, 8, GREEN)
    cv.rect(0, H - 8, W, 8, GREEN)
    cv.rect(0, 0, 8, H, GREEN)
    cv.rect(W - 8, 0, 8, H, GREEN)

    # Masthead.
    cv.rect(8, 8, W - 16, 118, GREEN)
    cv.text_centered(26, "THE WORLD TODAY", 8, WHITE)
    cv.text_centered(96, "WEDNESDAY, 25 NOVEMBER 2026", 3, GOLD)
    cv.hline(8, 126, W - 16, RED)
    cv.hline(8, 130, W - 16, RED)
    cv.text_centered(142, "SIX STORIES FROM AROUND THE GLOBE - ONE DAY IN THE WORLD", 2, INK)

    # Lead story, full width.
    lx, ly, lw, lh = 16, 168, W - 32, 204
    cv.rect(lx, ly, lw, lh, PANEL)
    cv.rect(lx, ly, lw, 3, RED)
    cv.hline(lx, ly + lh - 1, lw, LIGHT)
    cv.vline(lx + lw - 1, ly, lh, LIGHT)
    cv.text(lx + 16, ly + 14, LEAD["kicker"], 2, RED)
    ix, iy, isize = lx + lw - 164, ly + 34, 132
    cv.rect(ix - 6, iy - 6, isize + 12, isize + 12, LIGHT)
    draw_icon(cv, LEAD["icon"], ix, iy, isize, GREEN)
    tx = lx + 16
    tw = lw - 16 - 176
    lines = cv.wrap(LEAD["headline"], 4, tw)[:2]
    ty = ly + 44
    for line in lines:
        cv.text(tx, ty, line, 4, INK)
        ty += 30
    body_lines = cv.wrap(LEAD["body"], 2, tw)[:3]
    ty += 6
    for line in body_lines:
        cv.text(tx, ty, line, 2, MUTED)
        ty += 15
    cv.hline(lx + 16, ly + lh - 30, tw, LIGHT)
    cv.text(lx + 16, ly + lh - 22, LEAD["place"], 2, RED)

    # Grid: 2 columns x 2 rows.
    margin, gap = 16, 16
    pw = (W - 2 * margin - gap) // 2
    ph = 188
    for i, story in enumerate(GRID):
        col = i % 2
        row = i // 2
        x = margin + col * (pw + gap)
        y = 388 + row * (ph + gap)
        draw_panel(cv, x, y, pw, ph, story, i)

    # Wide story at the bottom.
    wx, wy, ww, wh = 16, 796, W - 32, 120
    cv.rect(wx, wy, ww, wh, PANEL)
    cv.rect(wx, wy, ww, 3, GREEN)
    cv.hline(wx, wy + wh - 1, ww, LIGHT)
    cv.vline(wx + ww - 1, wy, wh, LIGHT)
    cv.text(wx + 16, wy + 12, WIDE["kicker"], 2, RED)
    cv.text(wx + 16, wy + 38, WIDE["headline"], 3, INK)
    wbody = cv.wrap(WIDE["body"], 2, ww - 32)[:2]
    wty = wy + 66
    for line in wbody:
        cv.text(wx + 16, wty, line, 2, MUTED)
        wty += 15
    cv.text(wx + 16, wy + wh - 18, WIDE["place"], 2, RED)

    # News ticker band.
    cv.rect(8, 932, W - 16, 56, GREEN)
    ty = 940
    for line in TICKER:
        cv.text(16, ty, line, 2, WHITE)
        ty += 22

    # Footer.
    cv.text_centered(998, "25 NOVEMBER 2026  -  WORLD NEWS IN ONE PAGE", 2, INK)
    return cv.to_png()


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, "entry.png")
        with open(path, "wb") as f:
            f.write(build())
    except OSError:
        outdir = "out"
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, "entry.png")
        with open(path, "wb") as f:
            f.write(build())
    print("wrote " + path)


if __name__ == "__main__":
    main()
