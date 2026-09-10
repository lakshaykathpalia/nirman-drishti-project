# -*- coding: utf-8 -*-
"""Presentation diagrams for the NirmanDrishti SIH deck.

Drawn at 3x and downsampled, so edges and text stay crisp when a slide is
projected. Palette matches the dashboard so the deck reads as one system.
"""

import os, sys, math
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

S = 3                                   # supersample factor
F = "C:/Windows/Fonts/"

NAVY   = (15, 37, 68)
NAVY2  = (29, 59, 107)
NAVY6  = (36, 80, 143)
NAVYL  = (143, 180, 230)
INK    = (16, 21, 31)
INK2   = (86, 96, 122)
INK3   = (138, 147, 166)
PAPER  = (255, 255, 255)
TINT   = (242, 245, 250)
LINE   = (214, 222, 234)
CRIT   = (179, 38, 30)
CRITBG = (253, 242, 241)
AMBER  = (200, 149, 31)
AMBERD = (138, 90, 0)
AMBERBG= (253, 248, 236)
GREEN  = (27, 127, 75)
GREENBG= (241, 248, 244)


def font(name, size):
    return ImageFont.truetype(F + name, int(size * S))

def bold(sz):  return font("calibrib.ttf", sz)
def reg(sz):   return font("calibri.ttf", sz)
def mono(sz):  return font("consola.ttf", sz)
def serif(sz): return font("cambriab.ttf", sz)


class Canvas:
    def __init__(self, w, h, bg=PAPER):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.im)

    def rrect(self, x, y, w, h, r=6, fill=PAPER, outline=LINE, width=1.2):
        self.d.rounded_rectangle(
            [x * S, y * S, (x + w) * S, (y + h) * S], radius=int(r * S),
            fill=fill, outline=outline, width=max(1, int(width * S)))

    def rect(self, x, y, w, h, fill=None, outline=None, width=1.2):
        self.d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                         fill=fill, outline=outline, width=max(1, int(width * S)))

    def text(self, x, y, s, f, fill=INK, anchor="la", spacing=1.35, max_w=None):
        """Draws s at (x,y). If max_w given, wraps. Returns height used."""
        if max_w is None:
            self.d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)
            return (f.getbbox(s)[3] - f.getbbox(s)[1]) / S
        words, lines, cur = s.split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if self.d.textlength(t, font=f) / S <= max_w:
                cur = t
            else:
                if cur: lines.append(cur)
                cur = wd
        if cur: lines.append(cur)
        lh = (f.getbbox("Ag")[3] - f.getbbox("Ag")[1]) / S * spacing
        for i, ln in enumerate(lines):
            self.d.text((x * S, (y + i * lh) * S), ln, font=f, fill=fill, anchor=anchor)
        return lh * len(lines)

    def ctext(self, cx, y, s, f, fill=INK):
        self.d.text((cx * S, y * S), s, font=f, fill=fill, anchor="ma")

    def line(self, x1, y1, x2, y2, fill=LINE, width=1.4, dash=None):
        if not dash:
            self.d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=fill, width=max(1, int(width * S)))
            return
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L == 0: return
        ux, uy = dx / L, dy / L
        pos, on = 0.0, True
        while pos < L:
            seg = min(dash if on else dash * 0.7, L - pos)
            if on:
                self.d.line([(x1 + ux * pos) * S, (y1 + uy * pos) * S,
                             (x1 + ux * (pos + seg)) * S, (y1 + uy * (pos + seg)) * S],
                            fill=fill, width=max(1, int(width * S)))
            pos += seg
            on = not on

    def arrow(self, x1, y1, x2, y2, fill=NAVY6, width=1.6, head=7):
        self.line(x1, y1, x2, y2, fill=fill, width=width)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (2.6, -2.6):
            self.d.line([x2 * S, y2 * S,
                         (x2 + head * math.cos(ang + s)) * S,
                         (y2 + head * math.sin(ang + s)) * S],
                        fill=fill, width=max(1, int(width * S)))

    def circle(self, cx, cy, r, fill=NAVY, outline=None, width=1.2):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
                       fill=fill, outline=outline, width=max(1, int(width * S)))

    def chip(self, x, y, s, f=None, fg=NAVY2, bg=TINT, br=LINE, padx=6, padyt=3, padyb=3):
        f = f or mono(8)
        tw = self.d.textlength(s, font=f) / S
        th = (f.getbbox("Ag")[3] - f.getbbox("Ag")[1]) / S
        w, h = tw + padx * 2, th + padyt + padyb
        self.rrect(x, y, w, h, r=3, fill=bg, outline=br, width=1)
        self.d.text(((x + padx) * S, (y + padyt) * S), s, font=f, fill=fg)
        return w

    def title(self, t, sub=None):
        self.text(40, 30, t, serif(26), NAVY)
        if sub:
            self.text(40, 66, sub, reg(13), INK2)

    def save(self, name):
        p = os.path.join(OUT, name)
        self.im.resize((self.w, self.h), Image.LANCZOS).save(p, "PNG")
        print(f"  {name}  ({self.w}x{self.h})")


# ═══════════════════════ 1 · SYSTEM ARCHITECTURE ═══════════════════════════
c = Canvas(1600, 640)
c.title("System architecture", "Data sources through detection to the officer's screen")

BAND = [("DATA SOURCES", 40, 250), ("INGEST & STORE", 330, 300),
        ("DETECTION", 700, 340), ("DELIVERY", 1110, 450)]
for label, x, w in BAND:
    c.text(x, 112, label, bold(10), INK3)

# sources
src = [("MoSPI allocation dataset", "543 constituencies · CSV"),
       ("Works, tenders & bids", "sanction records"),
       ("PWD Schedule of Rates", "per-category ceilings")]
y = 140
for t, s in src:
    c.rrect(40, y, 250, 62, fill=TINT)
    c.text(56, y + 13, t, bold(12), NAVY, max_w=225)
    c.text(56, y + 34, s, reg(10.5), INK2, max_w=225)
    c.arrow(292, y + 31, 326, y + 31)
    y += 78

# ingest + schema
c.rrect(330, 140, 300, 278, fill=PAPER, outline=NAVY2, width=1.6)
c.text(348, 154, "SQLite relational store", bold(13), NAVY)
c.text(348, 176, "8 tables, foreign keys, indexes", reg(10.5), INK2)
tables = ["constituencies", "mps", "works", "contractors",
          "tenders", "bids", "pwd_benchmarks", "anomalies"]
ty = 202
for i, t in enumerate(tables):
    tx = 348 + (i % 2) * 145
    if i % 2 == 0 and i: ty += 26
    c.chip(tx, ty, t, mono(8.5))
c.text(348, 392, "Cartel detection is only possible because bids", reg(9.5), INK3, max_w=270)
c.text(348, 404, "join to both tenders and contractors.", reg(9.5), INK3, max_w=270)

c.arrow(634, 279, 694, 279)

# detectors
det = [("Spatial duplicate", "Haversine ≤ 100 m", CRIT),
       ("Collusive bidding", "co-bid graph, Jaccard", AMBERD),
       ("Cost above ceiling", "PWD SoR · Z-score", CRIT),
       ("Fund stagnation", "≥180 days, <20%", AMBERD)]
y = 140
for t, s, col in det:
    c.rrect(700, y, 340, 62, fill=PAPER)
    c.rect(700, y, 3.5, 62, fill=col)
    c.text(722, y + 13, t, bold(12), NAVY)
    c.text(722, y + 34, s, mono(9.5), INK2)
    y += 70

c.text(700, 428, "Every detector writes one row per finding, with the", reg(9.5), INK3, max_w=340)
c.text(700, 440, "arithmetic that produced it.", reg(9.5), INK3, max_w=340)

c.arrow(1044, 279, 1104, 279)

# delivery
c.rrect(1110, 140, 450, 278, fill=PAPER, outline=NAVY2, width=1.6)
c.text(1128, 154, "FastAPI  ·  REST + OpenAPI", bold(13), NAVY)
eps = ["/api/stats", "/api/works", "/api/anomalies", "/api/mps",
       "/api/benchmarks", "/api/cartel-network", "POST /api/trigger-audit"]
ey = 180
for i, e in enumerate(eps):
    c.chip(1128 + (i % 2) * 165, ey, e, mono(8.5))
    if i % 2: ey += 26
c.line(1128, 288, 1542, 288, fill=LINE)
c.text(1128, 300, "Web GIS dashboard", bold(12), NAVY)
for t in ["Severity-graded triage queue", "Leaflet map with risk pins",
          "Evidence modal per finding", "Print view for the case file"]:
    c.text(1128, 322 + ["Severity-graded triage queue", "Leaflet map with risk pins",
                        "Evidence modal per finding", "Print view for the case file"].index(t) * 20,
           "•  " + t, reg(11), INK2)

# feedback loop
c.line(1335, 424, 1335, 470, fill=NAVYL, width=1.4)
c.line(870, 470, 1335, 470, fill=NAVYL, width=1.4)
c.arrow(870, 470, 870, 442, fill=NAVYL)
c.text(1000, 476, "Officer triggers re-audit  ·  full run in ~110 ms", reg(10), INK3)

# footer note
c.rrect(40, 530, 1520, 76, fill=TINT)
c.text(58, 546, "Design principle", bold(11), NAVY)
c.text(58, 566, "No black-box component anywhere in the pipeline. Each alert stores a recomputable proof string — a measured "
                "distance, a rate ratio, a Jaccard overlap, a day count — so a District Magistrate can verify the finding "
                "independently before acting on it.", reg(11.5), INK2, max_w=1490)
c.save("d1-architecture.png")


# ═══════════════════════ 2 · DETECTION PIPELINE FLOW ═══════════════════════
c = Canvas(1600, 720)
c.title("Detection pipeline", "What happens between a sanction record and an officer's alert")

steps = [
    ("1", "INGEST", "Official MoSPI dataset parsed into the relational schema. Real portal data and demo fixtures stay in separate modules.", NAVY2),
    ("2", "SCAN", "Four engines query the tables. Each encodes one documented malpractice pattern with an explicit threshold.", NAVY6),
    ("3", "EVIDENCE", "Every hit writes an anomalies row carrying severity, a case reference, and the arithmetic that produced it.", AMBERD),
    ("4", "TRIAGE", "Findings are graded Critical / High / Advisory, mapped, and queued for the officer who can act.", CRIT),
]
x = 40
for n, t, d, col in steps:
    c.rrect(x, 120, 355, 210, fill=PAPER)
    c.rect(x, 120, 355, 4, fill=col)
    c.circle(x + 30, 158, 15, fill=col)
    c.ctext(x + 30, 149, n, bold(13), PAPER)
    c.text(x + 58, 148, t, bold(14), NAVY)
    c.text(x + 24, 190, d, reg(11.5), INK2, max_w=310)
    if x < 1100:
        c.arrow(x + 363, 225, x + 388, 225)
    x += 396

# detail row under each step
detail = [
    ["543 constituencies", "14 works (demo)", "4 tenders · 10 bids"],
    ["≤ 100 m radius", "≥ 2 shared tenders", "≥ 1.5× ceiling · Z>2.5", "≥ 180 days · <20%"],
    ["44.97 m measured", "Jaccard 3/3 = 100%", "₹54.0L vs ₹16.5L", "695 days at 5%"],
    ["2 Critical", "4 High", "84 Advisory"],
]
x = 40
for col_items in detail:
    y = 352
    for it in col_items:
        c.chip(x + 24, y, it, mono(9))
        y += 26
    x += 396

c.rrect(40, 500, 1520, 90, fill=AMBERBG, outline=(238, 223, 186))
c.text(58, 516, "Worked example — the Varanasi duplicate", bold(12), AMBERD)
c.text(58, 538,
       "Two borewells of the same category, sanctioned 50 days apart to two different contractors in Ward 12. "
       "Haversine distance between their GPS points is 44.97 m, inside the 100 m threshold, so the pair is flagged "
       "CRITICAL and the coordinate pairs are stored with the finding.", reg(11.5), INK, max_w=1490)
c.save("d2-pipeline.png")


# ═══════════════════════ 3 · THE FOUR ENGINES ══════════════════════════════
c = Canvas(1600, 940)
c.title("The four detection engines", "Each encodes one malpractice pattern documented by CAG audits and the OECD")

eng = [
    ("Spatial duplicate detection", CRIT, CRITBG,
     "The scam: one asset built, two bills raised at the same spot.",
     "Compares every pair of same-category works inside one constituency and measures the "
     "great-circle distance between their GPS coordinates.",
     ["Haversine formula", "threshold ≤ 100 m", "SQL + Python"],
     "Detected:  44.97 m apart  —  two borewells, Ward 12, Varanasi"),
    ("Collusive bidding detection", AMBERD, AMBERBG,
     "The scam: rivals agree who wins, and take turns.",
     "Builds a bipartite graph of contractors and tenders, then measures how often each pair "
     "appears in the same bidding pool and how far their histories overlap.",
     ["NetworkX bipartite graph", "≥ 2 shared tenders", "Jaccard index"],
     "Detected:  Jaccard 3/3 = 100%  —  three contractors, Patna Sahib"),
    ("Rate benchmark & cost outliers", CRIT, CRITBG,
     "The scam: the work is real, the price is not.",
     "Checks each sanctioned amount against the state PWD Schedule of Rates ceiling, then runs a "
     "standard-score test to catch outliers the rate table would miss.",
     ["PWD SoR ceiling", "ratio ≥ 1.5×", "Z-score > 2.5"],
     "Detected:  ₹54.0 L against a ₹16.5 L ceiling  —  3.27×, Jaipur Rural"),
    ("Fund stagnation monitoring", AMBERD, AMBERBG,
     "The failure: money released, nothing built.",
     "Measures elapsed days since sanction against reported physical progress, and tracks "
     "constituency balances that stay unspent.",
     ["SQL temporal query", "≥ 180 days", "< 20% progress"],
     "Detected:  695 days at 5% progress  —  community hall, Bengaluru South"),
]

y = 108
for name, col, bgc, scam, how, specs, found in eng:
    c.rrect(40, y, 1520, 190, fill=PAPER)
    c.rect(40, y, 4, 190, fill=col)
    c.text(70, y + 18, name, bold(16), NAVY)
    c.text(70, y + 46, scam, reg(12), col)
    c.text(70, y + 72, how, reg(11.5), INK2, max_w=780)
    sx = 70
    for sp in specs:
        sx += c.chip(sx, y + 130, sp, mono(9)) + 8
    c.rrect(900, y + 26, 640, 138, fill=bgc, outline=None)
    c.text(922, y + 44, "WHAT IT FOUND IN THE PROTOTYPE", bold(9.5), INK3)
    c.text(922, y + 68, found, mono(12.5), col, max_w=600)
    c.text(922, y + 116, "Stored with the finding as a recomputable proof string.", reg(10.5), INK2, max_w=600)
    y += 202
c.save("d3-engines.png")


# ═══════════════════════ 4 · CARTEL EXPLAINER ══════════════════════════════
c = Canvas(1600, 860)
c.title("How collusive bidding is detected",
        "Three contractors, three tenders, and a rotation no honest market produces")

# bipartite layout
cx_c, cx_t = 330, 900
cys = [230, 370, 510]
names = [("CONTR-05", "Magadh Buildcon"), ("CONTR-06", "Patliputra Engineering"), ("CONTR-07", "Maa Sharda Infra")]
tenders = [("TND-PAT-01", "Community hall", "₹23.50 L"),
           ("TND-PAT-02", "Village road", "₹15.80 L"),
           ("TND-PAT-03", "Health sub-centre", "₹44.00 L")]
winner = {0: 0, 1: 1, 2: 2}          # tender index -> winning contractor index

c.text(cx_c - 120, 150, "CONTRACTORS", bold(10), INK3)
c.text(cx_t - 60, 150, "TENDERS", bold(10), INK3)

# edges first
for ti, cy_t in enumerate(cys):
    for ci, cy_c in enumerate(cys):
        win = winner[ti] == ci
        c.line(cx_c + 118, cy_c + 22, cx_t - 62, cy_t + 22,
               fill=NAVY6 if win else (200, 208, 220),
               width=2.0 if win else 1.1, dash=None if win else 5)

for i, ((cid, nm), cy) in enumerate(zip(names, cys)):
    c.rrect(cx_c - 120, cy, 238, 46, fill=CRITBG, outline=(240, 207, 204))
    c.circle(cx_c - 98, cy + 23, 7, fill=CRIT)
    c.text(cx_c - 82, cy + 8, nm, bold(12), NAVY)
    c.text(cx_c - 82, cy + 26, cid, mono(9), INK2)

for i, ((tid, desc, amt), cy) in enumerate(zip(tenders, cys)):
    c.rrect(cx_t - 62, cy, 300, 46, fill=TINT, outline=LINE)
    c.text(cx_t - 44, cy + 8, desc, bold(12), NAVY)
    c.text(cx_t - 44, cy + 26, f"{tid}   won at {amt}", mono(9), INK2)

# legend
c.line(1180, 232, 1240, 232, fill=NAVY6, width=2.0)
c.text(1250, 224, "winning bid", reg(11), INK2)
c.line(1180, 258, 1240, 258, fill=(200, 208, 220), width=1.1, dash=5)
c.text(1250, 250, "losing (cover) bid", reg(11), INK2)

# the maths
c.rrect(1160, 300, 400, 216, fill=PAPER)
c.text(1182, 318, "The measurement", bold(13), NAVY)
c.text(1182, 346, "Co-bid count", reg(11), INK2)
c.text(1182, 364, "W(05,06) = 3 tenders  ≥ 2", mono(11), INK)
# No Windows system font ships a glyph for U+222A, so the union is spelled out.
c.text(1182, 394, "Jaccard overlap  (intersection ÷ union)", reg(11), INK2)
c.text(1182, 412, "3 shared  /  3 combined", mono(11), INK)
c.rrect(1182, 440, 356, 58, fill=CRITBG, outline=(240, 207, 204))
c.ctext(1360, 452, "100%", serif(24), CRIT)
c.text(1200, 482, "Neither ever bid without the other", reg(10.5), INK2)

# rotation table
c.rrect(40, 600, 1080, 210, fill=PAPER)
c.text(62, 618, "The rotation, bid by bid", bold(13), NAVY)
c.text(62, 640, "Each contractor wins exactly once; the other two quote just above. That is bid rotation with cover "
                "bidding — two of the four forms named in the OECD Bid-Rigging Detection List.", reg(11), INK2, max_w=1030)

col_x = [62, 340, 570, 800]
c.text(col_x[0], 690, "TENDER", bold(9.5), INK3)
for j, (cid, nm) in enumerate(names):
    c.text(col_x[j + 1], 690, cid, bold(9.5), INK3)
rows = [("TND-PAT-01", [("23.50", True), ("23.90", False), ("23.95", False)]),
        ("TND-PAT-02", [("15.95", False), ("15.80", True), ("15.98", False)]),
        ("TND-PAT-03", [("44.80", False), ("44.90", False), ("44.00", True)])]
ry = 714
for tid, bids in rows:
    c.line(62, ry - 6, 1098, ry - 6, fill=(237, 240, 245))
    c.text(col_x[0], ry, tid, mono(10.5), INK2)
    for j, (amt, win) in enumerate(bids):
        c.text(col_x[j + 1], ry, f"₹{amt} L", mono(10.5), CRIT if win else INK2)
        if win:
            c.chip(col_x[j + 1] + 62, ry - 3, "WON", mono(8), PAPER, CRIT, CRIT, padx=5, padyt=2, padyb=2)
    ry += 30

c.rrect(1160, 600, 400, 210, fill=AMBERBG, outline=(238, 223, 186))
c.text(1182, 618, "Stated honestly", bold(12), AMBERD)
c.text(1182, 642, "The detector compares pairs, not cliques. One ring of three contractors surfaces as three pairwise "
                  "relationships. Clique consolidation is on the roadmap.", reg(11), INK, max_w=356)
c.text(1182, 730, "Co-bidding alone is a flag for investigation — never a conviction.", reg(11), INK2, max_w=356)
c.save("d4-cartel.png")


# ═══════════════════════ 5 · DATA MODEL (ER) ═══════════════════════════════
c = Canvas(1600, 860)
c.title("Data model", "MPLADS records are inherently relational — that is what makes the detection possible")

boxes = {
    "constituencies": (60, 140, ["constituency_id  PK", "name · state", "total_allocated_cr", "unspent_balance_cr"]),
    "mps":            (60, 330, ["mp_id  PK", "name · house", "constituency_id  FK", "tenure_start / end"]),
    "works":          (450, 210, ["work_id  PK", "constituency_id  FK", "mp_id  FK", "contractor_id  FK",
                                  "work_category  FK", "sanctioned_amount_lakhs", "latitude · longitude",
                                  "completion_percent", "sanction_date"]),
    "contractors":    (450, 500, ["contractor_id  PK", "company_name · pan", "registered_district", "risk_score"]),
    "tenders":        (860, 210, ["tender_id  PK", "work_id  FK", "estimated_cost_lakhs", "winning_contractor_id  FK"]),
    "bids":           (860, 430, ["bid_id  PK", "tender_id  FK", "contractor_id  FK", "bid_amount_lakhs",
                                  "is_winning_bid"]),
    "pwd_benchmarks": (1240, 140, ["category  PK", "unit", "avg_rate_inr", "max_acceptable_rate_inr"]),
    "anomalies":      (1240, 380, ["anomaly_id  PK", "work_id  FK", "anomaly_type", "severity",
                                   "mathematical_evidence", "status"]),
}
HEAD = 30
for name, (x, y, fields) in boxes.items():
    h = HEAD + len(fields) * 22 + 12
    accent = CRIT if name == "anomalies" else (GREEN if name == "pwd_benchmarks" else NAVY2)
    c.rrect(x, y, 300, h, fill=PAPER)
    c.rrect(x, y, 300, HEAD, r=6, fill=accent, outline=accent)
    c.rect(x, y + HEAD - 6, 300, 6, fill=accent, outline=accent)
    c.text(x + 14, y + 8, name, bold(12), PAPER)
    for i, f in enumerate(fields):
        c.text(x + 14, y + HEAD + 8 + i * 22, f, mono(9.5),
               INK if ("PK" in f or "FK" in f) else INK2)

# Anchored on real box edges so no arrow lands inside a table or crosses one.
rel = [((360, 205), (450, 255)),      # constituencies -> works
       ((360, 395), (450, 330)),      # mps            -> works
       ((600, 500), (600, 456)),      # contractors    -> works
       ((750, 265), (860, 265)),      # works          -> tenders
       ((1010, 340), (1010, 424)),    # tenders        -> bids
       ((750, 545), (860, 505)),      # contractors    -> bids
       ((750, 330), (1240, 430))]     # works          -> anomalies
for (x1, y1), (x2, y2) in rel:
    c.arrow(x1, y1, x2, y2, fill=NAVYL, width=1.3, head=6)

# works.work_category -> pwd_benchmarks.category, routed above the tenders box
c.line(700, 210, 700, 112, fill=NAVYL, width=1.3)
c.line(700, 112, 1330, 112, fill=NAVYL, width=1.3)
c.arrow(1330, 112, 1330, 136, fill=NAVYL, width=1.3, head=6)

c.rrect(60, 700, 1480, 96, fill=TINT)
c.text(78, 718, "Why SQL and not a document store", bold(12), NAVY)
c.text(78, 740,
       "A member recommends a work; a work has a tender; a tender receives bids from contractors. Cartel detection is only "
       "possible because bids join to both tenders and contractors — in a document store those joins would be "
       "reimplemented by hand. Foreign keys also stop a finding from ever referencing a work that does not exist.",
       reg(11.5), INK2, max_w=1450)
c.save("d5-data-model.png")


# ═══════════════════════ 6 · COST vs CEILING ═══════════════════════════════
c = Canvas(1400, 620)
c.title("Cost benchmark check", "Sanctioned amount against the state PWD Schedule of Rates ceiling")

bx, bw, scale = 320, 780, 60.0
rows = [("Sanctioned amount", 54.0, CRIT, "₹54.00 L"),
        ("PWD ceiling for this category", 16.5, NAVY6, "₹16.50 L"),
        ("Typical rate (state average)", 12.0, (150, 160, 178), "₹12.00 L")]
y = 150
for label, val, col, amt in rows:
    c.text(60, y + 8, label, reg(12.5), INK)
    w = bw * (val / scale)
    c.rect(bx, y, bw, 34, fill=(246, 248, 251))
    c.rect(bx, y, w, 34, fill=col)
    c.text(bx + w + 14, y + 8, amt, bold(13), col)
    y += 62

# ceiling marker
cx = bx + bw * (16.5 / scale)
c.line(cx, 140, cx, 340, fill=INK, width=1.6, dash=6)
c.text(cx + 8, 330, "ceiling", mono(9.5), INK)

c.rrect(60, 380, 1280, 84, fill=CRITBG, outline=(240, 207, 204))
c.text(80, 396, "CC village road, 1.2 km — Shahpura Tehsil, Jaipur Rural", bold(13), NAVY)
c.text(80, 420, "Sanctioned at 3.27× the official ceiling — ₹37.50 lakh above the maximum permissible rate. "
                "Flagged CRITICAL with the ratio stored as evidence.", reg(11.5), INK, max_w=1240)

c.text(60, 490, "Evidence string written to the anomalies table", bold(10.5), INK3)
c.rrect(60, 512, 1280, 46, fill=TINT)
c.text(80, 527, "Sanctioned = Rs 54.0L, Max PWD Ceiling = Rs 16.5L. Price Ratio = 3.27x (Threshold is 1.5x).",
       mono(11), INK)
c.save("d6-cost-ceiling.png")

print("\nSaved to:", os.path.abspath(OUT))
