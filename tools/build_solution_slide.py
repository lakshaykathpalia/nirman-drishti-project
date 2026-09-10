# -*- coding: utf-8 -*-
"""Dense one-page 'Proposed Solution' slide for the SIH deck.

Laid out like a submission slide rather than a presentation slide: four banded
sections, real figures, no filler. Rendered at 3x and downsampled.
"""

import os, sys, math
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

S = 3
F = "C:/Windows/Fonts/"

CRIM   = (176, 20, 44)
CRIM_D = (138, 16, 35)
CRIM_L = (216, 142, 154)
TINT   = (252, 240, 242)
INK    = (17, 17, 20)
INK2   = (86, 92, 104)
INK3   = (140, 146, 158)
NAVY   = (15, 37, 68)
PAPER  = (255, 255, 255)
LINE   = (226, 230, 237)
GREEN  = (27, 127, 75)


def bahn(size, weight="Regular"):
    f = ImageFont.truetype(F + "bahnschrift.ttf", int(size * S))
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def cal(size, b=False):
    return ImageFont.truetype(F + ("calibrib.ttf" if b else "calibri.ttf"), int(size * S))


def mono(size):
    return ImageFont.truetype(F + "consola.ttf", int(size * S))


W, H = 1920, 1080
im = Image.new("RGB", (W * S, H * S), PAPER)
d = ImageDraw.Draw(im)


def text(x, y, s, f, fill=INK, anchor="la"):
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)


def wrap(x, y, s, f, fill=INK, max_w=600, lh=1.32):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) / S <= max_w:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    step = (f.getbbox("Ag")[3] - f.getbbox("Ag")[1]) / S * lh
    for i, ln in enumerate(lines):
        d.text((x * S, (y + i * step) * S), ln, font=f, fill=fill)
    return step * len(lines)


def rich(x, y, parts, f_reg, f_em, max_w=1000, lh=1.34, fill=INK, em=CRIM):
    """parts: list of (text, emphasised?). Wraps across the whole run."""
    toks = []
    for t, e in parts:
        for wd in t.split(" "):
            if wd: toks.append((wd, e))
    step = (f_reg.getbbox("Ag")[3] - f_reg.getbbox("Ag")[1]) / S * lh
    cx, cy = x, y
    space = d.textlength(" ", font=f_reg) / S
    for wd, e in toks:
        f = f_em if e else f_reg
        w = d.textlength(wd, font=f) / S
        if cx + w > x + max_w:
            cx = x; cy += step
        d.text((cx * S, cy * S), wd, font=f, fill=em if e else fill)
        cx += w + space
    return cy + step - y


def rrect(x, y, w, h, r=8, fill=PAPER, outline=None, width=1.2):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=int(r * S),
                        fill=fill, outline=outline, width=max(1, int(width * S)))


def rect(x, y, w, h, fill):
    d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S], fill=fill)


def band(x, y, label):
    """Section header: short crimson tab + label, as in the reference layout."""
    rect(x, y + 2, 5, 22, CRIM)
    text(x + 14, y, label, bahn(21, "Bold"), CRIM)
    return y + 34


def circle(cx, cy, r, fill, outline=None, width=2):
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
              fill=fill, outline=outline, width=max(1, int(width * S)))


M = 54                       # page margin

# ───────────────────────────── HEADER ────────────────────────────────────
text(M, 34, "«Team name»", bahn(26, "Bold"), CRIM)
text(W / 2, 22, "PROPOSED SOLUTION", bahn(46, "Bold"), INK, anchor="ma")

rrect(W - M - 300, 26, 300, 62, r=8, fill=TINT)
text(W - M - 280, 38, "SMART INDIA HACKATHON 2026", bahn(15, "Bold"), CRIM_D)
text(W - M - 280, 60, "PS SIH26102  ·  MoSPI  ·  Software", cal(12), INK2)

rect(M, 104, W - 2 * M, 1.5, LINE)

# ─────────────────────── 1 · THE PROBLEM IN NUMBERS ──────────────────────
y = band(M, 124, "The Problem, in Real Numbers")

stats = [
    ("₹1,788 Cr", "MPLADS funds lying unspent", "CAG audit, as on 31 Mar 2009"),
    ("543", "constituencies to audit by hand", "MoSPI · every year"),
    ("₹5 Cr", "released per MP, every year", "MPLADS Guidelines, 2023"),
]
cx = M
for big, lab, src in stats:
    rrect(cx, y, 276, 134, r=8, fill=TINT)
    text(cx + 22, y + 18, big, bahn(40, "Bold"), CRIM)
    wrap(cx + 22, y + 72, lab, cal(14.5), INK, max_w=236, lh=1.22)
    text(cx + 22, y + 106, src, cal(11.5), INK3)
    cx += 292

# Cost escalation on one real work — bars left, caption clear of them on the right.
bars = [("2022 rate", 12.0, CRIM_L), ("PWD ceiling", 16.5, (200, 96, 116)), ("Sanctioned", 54.0, CRIM)]
bw, gap, bx0 = 112, 74, 980
CH = 168
base = y + CH
bx = bx0
for lab, val, col in bars:
    bh = (val / 60.0) * (CH - 42)
    rect(bx, base - bh, bw, bh, col)
    text(bx + bw / 2, base - bh - 24, f"₹{val:.1f} L", bahn(17, "Bold"), INK, anchor="ma")
    text(bx + bw / 2, base + 9, lab, cal(12.5), INK2, anchor="ma")
    bx += bw + gap
rect(bx0 - 22, base, (bw + gap) * 3 - gap + 44, 1.5, (190, 196, 206))

wrap(1548, y + 26,
     "One 1.2 km village road, billed at 3.27× the official ceiling — flagged automatically",
     bahn(17, "Bold"), CRIM, max_w=318, lh=1.3)
wrap(1548, y + 118, "Shahpura Tehsil, Jaipur Rural · detected by the prototype",
     cal(12), INK3, max_w=318)

y += 176

# ─────────────────────── 2 · SOLUTION STATEMENT ──────────────────────────
y = band(M, y, "Solution Statement")

bullets = [
    [("Automated integrity auditing:", False), (" NirmanDrishti screens every MPLADS work the moment it is sanctioned, running", False),
     (" four detection engines over a relational store of works, tenders and bids", True),
     (" — a complete national audit in", False), (" under 110 milliseconds.", True)],
    [("Evidence, not scores:", False), (" every flag stores the arithmetic that produced it —", False),
     (" a measured GPS distance, a rate ratio, a Jaccard overlap, a day count", True),
     (" — so a District Magistrate can", False), (" recompute the finding before acting on it,", True),
     (" and it holds up in a departmental inquiry.", False)],
]
for b in bullets:
    circle(M + 8, y + 10, 4, INK)
    h = rich(M + 26, y, b, cal(17), cal(17, True), max_w=W - 2 * M - 34)
    y += h + 14

y += 26

# ─────────────────────── 3 · THE AUDIT PIPELINE ──────────────────────────
y = band(M, y, "How It Works — Audit Pipeline")

steps = [
    ("1", "Ingest", "543 constituencies"),
    ("2", "Normalise", "8-table SQL schema"),
    ("3", "Detect", "4 engines in parallel"),
    ("4", "Evidence", "proof string per flag"),
    ("5", "Triage", "Critical / High / Advisory"),
    ("6", "Act", "GIS map + case file"),
]
sx = M + 40
step_gap = (W - 2 * M - 80) / (len(steps) - 1)
for i, (n, t, sub) in enumerate(steps):
    cx = sx + i * step_gap
    first = i == 0
    circle(cx, y + 40, 38, CRIM if first else (238, 240, 244))
    text(cx, y + 19, n, bahn(33, "Bold"), PAPER if first else INK, anchor="ma")
    text(cx, y + 90, t, bahn(20, "Bold"), INK, anchor="ma")
    text(cx, y + 117, sub, cal(13), INK2, anchor="ma")
    if i < len(steps) - 1:
        ax = cx + 50
        tipx = ax + step_gap - 100
        d.line([ax * S, (y + 40) * S, tipx * S, (y + 40) * S],
               fill=(198, 204, 214), width=max(1, int(1.6 * S)))
        for s in (2.6, -2.6):
            d.line([tipx * S, (y + 40) * S,
                    (tipx + 9 * math.cos(s)) * S, (y + 40 + 9 * math.sin(s)) * S],
                   fill=(198, 204, 214), width=max(1, int(1.6 * S)))

y += 168

# ─────────────────────── 4 · CORE FEATURES ───────────────────────────────
y = band(M, y, "Core Features — What it Ships.")

feats = [
    ("Four detection engines.", "Duplicate assets, collusive bidding, cost above ceiling, stalled funds."),
    ("Explainable by construction.", "Every finding stores a recomputable proof string, not an opaque score."),
    ("Severity triage.", "2 Critical and 4 High kept separate from 84 advisory notices."),
    ("Live GIS surveillance.", "Leaflet map, risk-coloured pins, click-through to the evidence."),
    ("Tunable thresholds.", "All six live in one config file, set by the auditing authority."),
    ("Print-ready case file.", "Ctrl+P yields a clean report for the departmental file."),
]
col_w = (W - 2 * M) / 2 - 20
for i, (b, rest) in enumerate(feats):
    cx = M + (i % 2) * (col_w + 40)
    cy = y + (i // 2) * 44
    circle(cx + 8, cy + 10, 4, CRIM)
    bw_ = d.textlength(b, font=cal(16.5, True)) / S
    text(cx + 26, cy, b, cal(16.5, True), INK)
    text(cx + 30 + bw_, cy, rest, cal(16), INK2)

y += 3 * 44 + 22

rect(M, y, W - 2 * M, 1.5, LINE)
text(M, y + 14, "Prototype figures are live from the running system  ·  full audit 110 ms  ·  "
                "₹8,332.82 Cr and 543 constituencies ingested from the official MoSPI dataset",
     cal(13), INK3)

out = os.path.join(OUT, "slide-proposed-solution.png")
im.resize((W, H), Image.LANCZOS).save(out, "PNG")
print("wrote", out, f"({W}x{H})")
