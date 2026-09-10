# Presentation assets

Screenshots captured from the running prototype and diagrams drawn to match the dashboard's
palette, so slides and live demo read as one system.

**Regenerate everything:** start the server (`python run.py`), then run the two scripts noted at
the bottom. Screenshots are 3000 px wide (2× device scale) — they stay sharp when projected.

---

## Where each asset goes in the SIH deck

| Slide | Asset | What it shows |
| :-- | :-- | :-- |
| 2 · Proposed Solution | `01-overview.png` | The dashboard at rest — 6 confirmed findings, triage ladder, both charts |
| 2 · Proposed Solution | `08-evidence-modal.png` | Stored proof for one finding — the explainability claim, made concrete |
| 3 · Technical Approach | `d1-architecture.png` | Sources → SQL store → four detectors → API → dashboard |
| 3 · Technical Approach | `d2-pipeline.png` | Ingest → Scan → Evidence → Triage, with real values at each stage |
| 3 · Technical Approach | `d5-data-model.png` | The eight tables and their foreign keys |
| 3 or 4 · Detectors | `d3-engines.png` | All four engines with method, threshold and what each found |
| 4 · Feasibility | `06-methodology.png` | The in-product methodology page, including stated limitations |
| 5 · Impact | `d6-cost-ceiling.png` | ₹54.00 L against a ₹16.50 L ceiling — the most legible finding |
| 5 · Impact | `d4-cartel.png` | The bid-rotation explainer with the full bid table |
| 5 · Impact | `03-map.png` | National GIS view with severity-coloured pins |
| Appendix / backup | `02-findings.png` | Findings register |
| Appendix / backup | `04-projects.png` | Projects register |
| Appendix / backup | `05-mp-directory.png` | 543-member allocation directory — proof the real dataset is loaded |
| Appendix / backup | `07-overview-full.png` | Full-height Overview, for a scrolling walkthrough |
| Appendix / backup | `09-cartel-network.png` | Live NetworkX graph, cropped to the connected component |
| Appendix / backup | `10-cartel-panel.png` | Map view with the co-bidding panel below it |

---

## Prototype screenshots

| File | Size | Notes |
| :-- | :-- | :-- |
| `01-overview.png` | 3000×1880 | Audit Overview |
| `02-findings.png` | 3000×1880 | Findings register |
| `03-map.png` | 3000×1880 | Geospatial map, tiles fully loaded |
| `04-projects.png` | 3000×1880 | Projects register |
| `05-mp-directory.png` | 3000×1880 | MP directory |
| `06-methodology.png` | 3000×1880 | Methodology page |
| `07-overview-full.png` | 3000×4344 | Full-page Overview |
| `08-evidence-modal.png` | 3000×1880 | Evidence modal open |
| `09-cartel-network.png` | 2396×682 | Graph panel only |
| `10-cartel-panel.png` | 3000×1880 | Map view scrolled to graph |

## Diagrams

| File | Size |
| :-- | :-- |
| `d1-architecture.png` | 1600×640 |
| `d2-pipeline.png` | 1600×720 |
| `d3-engines.png` | 1600×940 |
| `d4-cartel.png` | 1600×860 |
| `d5-data-model.png` | 1600×860 |
| `d6-cost-ceiling.png` | 1400×620 |

---

## Figures shown in these assets

Captured 10 September 2026 against the live database. If you re-run the audit, the stagnation
day count increases — everything else is stable.

- 6 confirmed findings (2 Critical, 4 High) · 84 advisory · 90 alerts total
- ₹150.15 L sanctioned value at risk · ₹37.50 L largest overcharge
- 543 constituencies · ₹8,332.82 Cr tracked · 14 works audited
- Full audit runtime ≈ 110 ms

---

## Regenerating

```bash
python run.py                       # server must be running for screenshots
python <scratch>/shots.py docs/assets
python <scratch>/diagrams.py docs/assets
```

Screenshots need `playwright` plus its Chromium build (`python -m playwright install chromium`).
Diagrams need only Pillow. Neither is a runtime dependency of the project, so neither is in
`requirements.txt`.

**Note on typography:** no Windows system font ships a glyph for the set-union symbol (U+222A),
so `d4-cartel.png` spells the Jaccard formula out as "intersection ÷ union" rather than rendering
an empty box.
