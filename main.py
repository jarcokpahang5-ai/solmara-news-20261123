#!/usr/bin/env python3
"""Solmara News — 23 November 2026 world news poster.

Draws a 1024x1024 newspaper front page as a PNG using only the Python
standard library (zlib + struct for the PNG encoder, a hand-built 5x7
bitmap font for text). No network, no third-party packages.
Deterministic: identical input always produces identical bytes.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER = (247, 243, 232)
INK = (26, 36, 51)
RED = (178, 38, 30)
TEAL = (15, 96, 104)
GOLD = (176, 132, 46)
LIGHT = (233, 226, 208)
MIDGREY = (120, 116, 104)
WHITE = (255, 255, 255)
DARKRED = (122, 22, 18)

# --- 5x7 bitmap font -------------------------------------------------------
# Each glyph: 7 rows of 5 bits, '#' = on.
GLYPHS = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
BLANK = ("00000",) * 7


def text_width(text, scale):
    """Pixel width of text at given scale (6 px advance per char)."""
    return len(text) * 6 * scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text.upper():
            glyph = GLYPHS.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, text, scale, color):
        x = cx - text_width(text, scale) // 2
        return self.draw_text(x, y, text, scale, color)

    def paragraph(self, x, y, text, scale, color, max_width, leading=None):
        if leading is None:
            leading = 9 * scale
        for line in wrap_text(text, max_width, scale):
            self.draw_text(x, y, line, scale, color)
            y += leading
        return y


# --- PNG encoder -----------------------------------------------------------
def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        start = y * stride
        raw += canvas.px[start:start + stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# --- content ---------------------------------------------------------------
LEAD = {
    "kicker": "CLIMATE  |  COP31",
    "headline": "COP31 COLLAPSES WITH NO DEAL",
    "summary": ("The final draft avoids mentioning \"fossil fuels\" as "
                "delegates from nearly 200 countries fail to agree."),
}

STORIES = [
    {
        "kicker": "MIDDLE EAST",
        "color": RED,
        "headline": "HORMUZ WAR ENTERS CRUCIAL STAGE",
        "summary": ("The Iran-US war engulfs Saudi Arabia and Bahrain. "
                    "Iran says it hit two Patriot radars at a US base "
                    "in Bahrain."),
    },
    {
        "kicker": "EUROPE",
        "color": TEAL,
        "headline": "RUSSIAN SHIP STILL BURNING OFF FINLAND",
        "summary": ("Russian cargo ship still burning off Finland; a "
                    "Russian warship is sunk in Libya by a suspected "
                    "Ukrainian drone."),
    },
    {
        "kicker": "MEXICO",
        "color": RED,
        "headline": "KINGPIN 'EL CHAPO ISIDRO' CAPTURED",
        "summary": ("Fausto Isidro Meza Flores is seized in a Sinaloa "
                    "raid; eleven people are killed in firefights."),
    },
    {
        "kicker": "UNITED STATES",
        "color": TEAL,
        "headline": "FBI PROBES APPARENT NCIC DATABASE HACK",
        "summary": ("FBI probes an apparent hack of its NCIC criminal "
                    "database; Trump appeared to confirm it on TV."),
    },
    {
        "kicker": "UNITED STATES",
        "color": RED,
        "headline": "DEMOCRATS WIN BIGGEST HOUSE MAJORITY SINCE 1992",
        "summary": ("Democrats win at least 258 House seats, their "
                    "biggest majority since 1992."),
    },
]

BRIEFS = [
    "INDONESIA FACTORY FIRE KILLS THREE.",
    "S. KOREA MINISTER QUITS OVER AI EXAM.",
    "INDIA'S RECORD 720/9 IN WELLINGTON.",
    "VERSTAPPEN WINS CHAOTIC LAS VEGAS GP.",
    "NEPAL PM SHAH HOLDS TALKS WITH MODI.",
    "UN KEEPS TALKING ON LETHAL AI ARMS.",
    "14 MISSING AFTER KYIV DRONE STRIKE.",
]


# --- layout ----------------------------------------------------------------
def build():
    c = Canvas(W, H, PAPER)
    M = 36                      # margin
    inner = W - 2 * M           # 952

    # --- masthead ----------------------------------------------------------
    c.hline(M, 26, inner, INK, 4)
    c.text_centered(W // 2, 44, "THE SOLMARA GAZETTE", 7, INK)
    c.hline(M, 108, inner, RED, 3)
    c.draw_text(M, 122, "MONDAY 23 NOVEMBER 2026", 2, RED)
    right = "WORLD NEWS  |  ONE PAGE"
    c.draw_text(W - M - text_width(right, 2), 122, right, 2, MIDGREY)
    c.hline(M, 146, inner, INK, 2)

    # --- lead story --------------------------------------------------------
    y = 160
    c.rect(M, y, inner, 8, RED)
    y += 16
    c.draw_text(M, y, LEAD["kicker"], 2, RED)
    y += 24
    y = c.paragraph(M, y, LEAD["headline"], 5, INK, inner, leading=42)
    y += 4
    y = c.paragraph(M, y, LEAD["summary"], 3, INK, inner, leading=30)
    y += 12
    c.hline(M, y, inner, INK, 2)
    y += 16

    # --- story grid: 2 columns, stories 0-3; story 4 full width ----------
    gap = 20
    col_w = (inner - gap) // 2

    def block_height(s, width):
        hl = len(wrap_text(s["headline"], width, 3))
        sl = len(wrap_text(s["summary"], width, 2))
        return 34 + hl * 26 + 4 + sl * 20

    def story_block(x, top, s, width):
        c.rect(x, top, width, 3, s["color"])
        c.draw_text(x, top + 10, s["kicker"], 2, s["color"])
        hy = c.paragraph(x, top + 34, s["headline"], 3, INK, width,
                         leading=26)
        c.paragraph(x, hy + 4, s["summary"], 2, MIDGREY, width, leading=20)

    for row in range(2):
        a, b = STORIES[row * 2], STORIES[row * 2 + 1]
        rh = max(block_height(a, col_w), block_height(b, col_w))
        story_block(M, y, a, col_w)
        story_block(M + col_w + gap, y, b, col_w)
        y += rh
        if row == 0:
            y += 8
            c.hline(M, y, inner, LIGHT, 2)
            y += 10
    y += 12

    # story 5: full width band with gold rule
    s = STORIES[4]
    c.hline(M, y, inner, GOLD, 3)
    c.draw_text(M, y + 12, s["kicker"], 2, s["color"])
    hy = c.paragraph(M, y + 36, s["headline"], 3, INK, inner, leading=26)
    y = c.paragraph(M, hy + 4, s["summary"], 2, MIDGREY, inner, leading=20)
    y += 12
    c.hline(M, y, inner, INK, 2)
    y += 14

    # --- briefs ------------------------------------------------------------
    c.rect(M, y, 150, 30, INK)
    c.draw_text(M + 12, y + 8, "BRIEFS", 2, WHITE)
    y += 44
    half = (len(BRIEFS) + 1) // 2
    col_end = y
    for col in range(2):
        by = y
        for i in range(col * half, min((col + 1) * half, len(BRIEFS))):
            x = M + col * (col_w + gap)
            c.rect(x, by + 3, 8, 8, RED if col == 0 else TEAL)
            by = c.paragraph(x + 16, by, BRIEFS[i], 2, INK, col_w - 16,
                             leading=20)
            by += 8
        col_end = max(col_end, by)
    y = col_end + 6

    # --- footer ------------------------------------------------------------
    c.hline(M, H - 52, inner, INK, 2)
    c.text_centered(W // 2, H - 40,
                    "ALL STORIES VERIFIED FROM PUBLIC REPORTING", 2, MIDGREY)
    c.text_centered(W // 2, H - 22,
                    "THE SOLMARA GAZETTE  -  23 NOVEMBER 2026", 2, MIDGREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "entry.png")
    canvas = build()
    write_png(out, canvas)
    print("wrote", out)


if __name__ == "__main__":
    main()
