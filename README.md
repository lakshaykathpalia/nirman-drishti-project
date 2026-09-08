# 🛡️ NirmanDrishti (निर्माण दृष्टि)

**Automated integrity auditing for the MPLADS scheme** — Problem Statement **SIH26102** (Ministry of Statistics and Programme Implementation).

Under MPLADS, every Member of Parliament recommends local development works — roads, community halls, borewells, classrooms, health centres. Across 543 constituencies this produces far more sanctions, tenders, bids and progress reports than officials can review by hand. NirmanDrishti loads that data into a relational database and runs four detectors that each encode one known malpractice pattern, surfacing the suspicious cases on a GIS dashboard with the supporting arithmetic attached to every alert.

---

## Quick start

```bash
pip install -r requirements.txt
```

```bash
python run.py
```

The launcher initialises the database, ingests the portal dataset, runs all four detectors, starts the API server and opens **http://localhost:8000** in your browser.

Requires **Python 3.10+**. No other services or setup needed — storage is a local SQLite file.

---

## Project layout

```
nirmandrishti/
├── run.py                      One-click launcher (seed → audit → serve)
├── requirements.txt
├── data/
│   └── mp_allocations.csv      Official MoSPI allocation dataset (543 MPs)
├── backend/
│   ├── config.py               ★ All detector thresholds and paths
│   ├── database.py             SQL schema, connection factory, indexes
│   ├── main.py                 FastAPI app and /api endpoints
│   ├── seed_data.py            Seeding orchestrator
│   ├── ingest/
│   │   └── portal_csv.py       REAL government data ingestion
│   ├── seed/
│   │   └── demo_scenarios.py   SYNTHETIC fraud fixtures (demo only)
│   └── detectors/
│       ├── spatial_detector.py
│       ├── cartel_detector.py
│       ├── price_anomaly.py
│       └── stagnation_detector.py
└── frontend/                   Leaflet GIS dashboard (vanilla JS)
```

**Real vs. synthetic data.** `backend/ingest/` holds genuine published MoSPI portal data — 543 constituencies, sitting members, and official allocation amounts. `backend/seed/` holds hand-authored fraud scenarios used to demonstrate each detector. The two are deliberately kept in separate modules so nothing synthetic is ever presented as official.

---

## The four detectors

| Detector | Malpractice | Method | Threshold |
|---|---|---|---|
| `spatial_detector` | Ghost / duplicate assets | Haversine great-circle distance between same-category works in one constituency | ≤ 100 m |
| `cartel_detector` | Bid rigging, cover bidding | NetworkX graph; edge weight = tenders two contractors co-bid on | ≥ 2 shared |
| `price_anomaly` | Inflated billing | Sanctioned amount vs. PWD Schedule of Rates ceiling, plus a Z-score outlier check | ≥ 1.5× / Z > 2.5 |
| `stagnation_detector` | Idle funds, stalled works | Days since sanction vs. completion percentage | ≥ 180 days at < 20% |

Every threshold above lives in [`backend/config.py`](backend/config.py) — tuning audit sensitivity for a smaller district is a single-file change.

Each detector writes to the shared `anomalies` table with a `mathematical_evidence` column, so every flag carries the GPS distance, rate ratio or co-bid count that produced it. The system is deliberately rule-based and statistical rather than a neural network: in a corruption inquiry, an alert an officer cannot verify is an alert that cannot be acted on.

---

## API

| Method | Endpoint | Returns |
|---|---|---|
| `GET` | `/api/stats` | Dashboard summary counters |
| `GET` | `/api/mps` | Directory of all 543 MPs and allocations |
| `GET` | `/api/works` | Sanctioned works with coordinates and risk level |
| `GET` | `/api/anomalies` | Detected flags with evidence |
| `GET` | `/api/cartel-network` | Contractor/tender graph for visualisation |
| `POST` | `/api/trigger-audit` | Re-runs all four detectors |
| `POST` | `/api/reset-data` | Rebuilds the database from source data |

Interactive OpenAPI docs are served at `/docs`.

---

## Database schema

```
constituencies ──< mps ──< works >── contractors
                            │            │
                            └──< tenders ──< bids
                    pwd_benchmarks (reference rates)
                    anomalies (detector output)
```

MPLADS data is inherently relational — an MP recommends a work, a work has a tender, a tender receives bids from contractors. SQL gives foreign-key integrity and fast indexed lookups, and cartel detection is only possible *because* bids join to both tenders and contractors.

---

## Known limitations

Stated plainly, because they matter when reading the output:

- **Idle-funds alerts are advisory, and the balances behind them are synthetic.** The published allocation dataset carries no expenditure column, so each constituency's unspent balance is generated from a stable hash of its name (see `demo_unspent_ratio` in `backend/ingest/portal_csv.py`). The rule requires both a ≥ 40% unspent ratio and a ≥ ₹2 Cr balance, which flags 84 of 543 constituencies. Replace the seed with real PFMS expenditure data and this becomes a genuine finding rather than a demonstration.
- **Cartel detection reports pairs, not rings.** A colluding trio surfaces as its three pairwise edges rather than one group. Clique detection is not yet implemented.
- **The works table is demo-scale.** 543 constituencies are real; the 14 works are fixtures. The spatial detector is O(n²) and would need spatial bucketing before running at national scale.
- **No machine-learning model is used.** Price outliers use a hand-computed Z-score. There is no Isolation Forest in this codebase.

---

## Roadmap

- Have detectors return `Finding` objects instead of writing to the database directly, so they can be unit-tested without mutating state
- Real `pytest` suite against a temporary database
- Clique-based cartel detection; bucketed spatial indexing
- Integration with the e-SAKSHI portal and PFMS via the existing REST endpoints
