# -*- coding: utf-8 -*-
"""Capture presentation-quality screenshots of the running NirmanDrishti dashboard."""

import os, sys, time
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
URL = "http://localhost:8000"
os.makedirs(OUT, exist_ok=True)

# 2x device scale => crisp when placed on a slide
VIEW = {"width": 1500, "height": 940}

SHOTS = [
    ("01-overview",        "dashboard", None,   "Audit Overview — KPIs, severity triage, charts"),
    ("02-findings",        "findings",  None,   "Findings register with evidence"),
    ("03-map",             "map",       None,   "Geospatial asset surveillance"),
    ("04-projects",        "works",     None,   "Sanctioned projects register"),
    ("05-mp-directory",    "mps",       None,   "543-member allocation directory"),
    ("06-methodology",     "method",    None,   "Detection engines and stated limitations"),
]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport=VIEW, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(2500)

    for name, view, _, caption in SHOTS:
        pg.evaluate(f"switchView('{view}')")
        if view == "map":
            pg.evaluate("mapInstance && mapInstance.invalidateSize()")
            pg.wait_for_timeout(3500)   # tiles
        else:
            pg.wait_for_timeout(900)
        pg.evaluate("window.scrollTo(0,0)")
        pg.wait_for_timeout(400)
        path = os.path.join(OUT, f"{name}.png")
        pg.screenshot(path=path)
        print(f"  {name}.png  — {caption}")

    # Full-page overview (everything below the fold too)
    pg.evaluate("switchView('dashboard')")
    pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(OUT, "07-overview-full.png"), full_page=True)
    print("  07-overview-full.png  — full Overview page, top to bottom")

    # Evidence modal open — the single most persuasive screen
    pg.evaluate("switchView('findings')")
    pg.wait_for_timeout(700)
    pg.evaluate("viewEvidence(0)")
    pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(OUT, "08-evidence-modal.png"))
    print("  08-evidence-modal.png  — stored mathematical evidence for one finding")

    # Cartel network graph, zoomed to the panel
    pg.evaluate("closeModal(); switchView('map')")
    pg.wait_for_timeout(2500)
    el = pg.query_selector("#cartel-network")
    if el:
        el.screenshot(path=os.path.join(OUT, "09-cartel-network.png"))
        print("  09-cartel-network.png  — contractor co-bidding graph")

    b.close()

print("\nSaved to:", os.path.abspath(OUT))
