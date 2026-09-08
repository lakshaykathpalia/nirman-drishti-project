# 🛡️ NirmanDrishti (निर्माण दृष्टि) — Complete Plain-English Guide & Jury Cheat-Sheet

**Problem Statement:** SIH26102 (Ministry of Statistics and Programme Implementation — MoSPI)
**Core Technologies:** Python (FastAPI, NetworkX), SQL (relational schema + Haversine spatial maths), interactive Web GIS.

> **Accuracy note.** Every claim in this document has been checked against the code in this
> repository. If you change a detector, update the matching section here. Nothing in this file
> describes a feature that is not actually implemented — see §6 for what the system does *not* do.

---

## 🌟 1. The Big Picture (Explained Like You're 10 Years Old)

Imagine the Indian Government gives your local Member of Parliament (MP) a budget every year to build schools, borewells, community halls, and streetlights in your area.

Because there are **thousands of projects across 543 parliamentary constituencies**, government auditors cannot visit every single street every day. So dishonest contractors and corrupt middlemen try to pull 4 classic tricks:

1. **The Ghost / Clone Trick:** They build 1 borewell, but submit bills for 2 borewells at the exact same street corner and pocket the extra money.
2. **The Secret Gang Trick (Cartels):** Three contractor friends pretend to compete for tenders, but secretly agree beforehand who will win and keep tender prices high.
3. **The Crazy Price Trick:** A rural road that normally costs ₹16 lakh is billed for ₹54 lakh.
4. **The Sleeping Money Trick:** Crores are sent to a district for a community hall, but the money sits untouched while work never starts.

### 💡 What Our System Does

**NirmanDrishti is an automated digital auditor.** It loads the government registers into a SQL database and runs 4 detection engines to catch all 4 tricks. It then puts warning pins on an interactive map for the District Magistrate and MoSPI officers to act on.

Crucially, **every alert stores the arithmetic that produced it** — the measured distance, the rate ratio, the co-bid count, the number of idle days — so an officer can independently recompute the finding before acting on it.

---

## 🔍 2. How the 4 Detection Engines Work (No Jargon!)

### 📍 1. The Spatial Duplicate Detector (`backend/detectors/spatial_detector.py`)

* **The Scam:** A contractor charges ₹1.15L for a borewell in Varanasi, and 50 days later charges ₹1.18L for another borewell just **45 metres away**.
* **How Our Code Catches It:**
  1. We fetch all works and compare every pair that shares the **same category** and the **same constituency**.
  2. We run the **Haversine formula**, which measures the curved (great-circle) distance between two GPS points.
  3. If distance ≤ **100 metres**, the code raises a **CRITICAL** flag: *"High-Density Duplicate Sanction"*.
* **The Math You Tell Judges:**

  $$\text{Distance} = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta\text{lon}}{2}\right)}\right)$$

  *(The code uses the mathematically equivalent `atan2` form, which is more numerically stable at small distances. Earth radius R = 6,371,000 m.)*

* **In simple words:** "We measure straight-line GPS distance on the globe and flag any two identical asset types within 100 metres of each other."
* **Real detected case:** `Haversine GPS Distance: 44.97m <= 100.0m threshold.`

---

### 🕸️ 2. The Cartel & Bid-Rigging Collusion Detector (`backend/detectors/cartel_detector.py`)

* **The Scam:** In Patna Sahib, Contractors A, B, and C always bid together on every tender. In Tender 1, A wins while B and C quote slightly higher "cover" bids. In Tender 2, B wins. In Tender 3, C wins.
* **How Our Code Catches It:**
  1. We use **NetworkX** to build a **bipartite graph** — contractors and tenders are nodes, bids are edges.
  2. For every **pair** of contractors, we count how many tenders they both bid on. That count becomes the edge weight.
  3. If two contractors have co-bid on **2 or more** tenders, the code flags the relationship as **HIGH** severity.
* **What You Tell Judges:**
  *"We model the procurement ecosystem as a bipartite graph and compute co-bidding weights between every pair of contractors. Repeated co-bidding with rotating winners and razor-thin margins is the signature of cover bidding."*

> ⚠️ **Say "co-bidding relationships", not "cliques" or "rings".**
> The code compares **pairs**, not groups. Our 3 alerts are the 3 pairwise edges of **one** group
> of 3 contractors (CONTR-05, 06, 07). The accurate phrasing is: *"one ring of three contractors,
> surfaced as three co-bidding relationships."* Clique consolidation is **not** implemented.

> ⚠️ **Do not use the word "Jaccard".**
> The stored evidence string ends with `Jaccard Bidding Overlap: 75.0%`. That figure is actually
> `shared_tenders ÷ total_tenders` — which is **not** the Jaccard index (intersection over *union*).
> The label is wrong. If a judge asks, own it: *"That label is incorrect in our output string — the
> figure is the share of all tenders both contractors bid on."*

---

### 💰 3. The Price Inflation Detector (`backend/detectors/price_anomaly.py`)

* **The Scam:** In Jaipur Rural, a 1.2 km village road is billed at ₹54 lakh, when the Public Works Department (PWD) benchmark ceiling is only ₹16.5 lakh — a ratio of **3.27×**.
* **How Our Code Catches It — two independent checks:**
  1. **Rule-based ceiling check.** We store the official **PWD Schedule of Rates (SoR)** in a SQL table for every category (per km of road, per classroom, per high-mast light). The code compares the sanctioned amount against the maximum allowed rate. Flagged at **1.5× or above**.
  2. **Statistical outlier check.** We compute the **Z-score** of each sanctioned cost against the mean and standard deviation of all costs, and flag anything above **2.5 standard deviations**.
* **What You Tell Judges:**
  *"We combine deterministic PWD Schedule of Rates validation with a standard-score outlier test. The ceiling check needs a benchmark; the Z-score does not — so it still catches inflation in categories where the rate table is missing or outdated."*
* **Real detected case:** `Sanctioned = Rs 54.0L, Max PWD Ceiling = Rs 16.5L. Price Ratio = 3.27x.`

> ⚠️ **There is no Isolation Forest and no scikit-learn in this project.**
> The statistical check is a hand-written Z-score in plain Python (`price_anomaly.py`, §2).
> Only three third-party packages are installed: **fastapi**, **uvicorn**, **networkx**.
> Never claim a machine-learning model you cannot open and show.

---

### ⏳ 4. The Fund Stagnation Monitor (`backend/detectors/stagnation_detector.py`)

* **The Inefficiency:** A community hall in Bengaluru South was sanctioned in October 2024 and is still at **5% progress**, now more than **690 days** later. Separately, ₹5.14 crore of that constituency's ₹14.7 crore allocation remains unspent.
* **How Our Code Catches It:**
  1. A SQL query selects works below the completion threshold (`completion_percent < 20`).
  2. Python computes elapsed days as `today − sanction_date`.
  3. If elapsed ≥ **180 days** and progress < **20%**, it raises a **HIGH** severity alert.
  4. A second, constituency-level rule reports unspent balances at or above **₹2.00 crore**.
* **What You Tell Judges:**
  *"We use SQL date filtering combined with elapsed-time computation to identify capital that has been released but not deployed."*
* **Real detected case:** `Elapsed Days = 693 >= 180 Threshold. Progress = 5%.`
  *(This number grows daily — it is computed from the current date, so quote whatever the screen shows.)*

> ⚠️ **The unspent-balance rule currently fires on almost every constituency.**
> Our demo seed gives every constituency the same 35% unspent ratio, so 542 of the 543 clear the
> ₹2 crore threshold. These are reported in a **separate advisory tier** and excluded from headline
> counts. Always say **"6 confirmed findings"**, never "548 anomalies".

---

## ⚙️ 3. Where Every Threshold Lives

All six thresholds are in a single file — `backend/config.py`. Tuning audit sensitivity for a smaller district is a one-file change, and no detection logic is touched.

| Detector | Threshold | Constant |
| :--- | :--- | :--- |
| Spatial duplicate | ≤ 100 m | `SPATIAL_DUPLICATE_RADIUS_METERS` |
| Collusive bidding | ≥ 2 shared tenders | `CARTEL_MIN_SHARED_TENDERS` |
| Price inflation | ≥ 1.5× PWD ceiling | `PRICE_INFLATION_MULTIPLIER` |
| Cost outlier | Z > 2.5 | `PRICE_OUTLIER_Z_SCORE` |
| Stagnation | ≥ 180 days, < 20% | `STAGNATION_IDLE_DAYS` |
| Idle funds | ≥ ₹2.00 Cr unspent | `IDLE_FUNDS_THRESHOLD_CR` |

---

## 🚀 4. How to Run the Project on Your Laptop

1. Open PowerShell or Command Prompt in the project folder:
   ```bash
   cd "D:\nirman drishti"
   ```
2. Install the three dependencies (first time only):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the one-click launcher:
   ```bash
   python run.py
   ```
4. Your browser opens automatically at **`http://localhost:8000`**.

Requires **Python 3.10+**. No database server, no build step, no API keys.
If the dashboard looks dark and neon, press **Ctrl+Shift+R** — that is a stale browser cache.

---

## 📊 5. The Numbers (verified against the running system)

| Figure | Value |
| :--- | :--- |
| Confirmed findings | **6** (2 critical, 4 high) |
| Advisory notices | 542 (unspent-balance tier) |
| Sanctioned value at risk | **₹150.15 lakh** |
| Largest single overcharge | **₹37.50 lakh** above ceiling (Jaipur Rural) |
| Constituencies ingested | **543** (real MoSPI dataset) |
| Total allocation tracked | **₹8,332.82 crore** |
| Works audited | 14 (synthetic demo fixtures) |
| Full audit runtime | **~110 milliseconds** |

**Which data is real:** the 543 constituencies, their sitting members, and the allocation amounts come from the official published MoSPI dataset (`data/mp_allocations.csv`). The 14 sanctioned works, 9 contractors, 4 tenders and 10 bids are **synthetic fixtures** written to exercise each detector. The code keeps these strictly separate — `backend/ingest/` for real data, `backend/seed/` for fixtures.

---

## 🚧 6. What the System Does *Not* Do (state this honestly)

1. **No machine-learning model.** Detection is rule-based plus one Z-score. This is deliberate: in a corruption inquiry, a finding an officer cannot recompute cannot be acted on.
2. **Cartel detection reports pairs, not rings.** Clique consolidation is not implemented.
3. **The advisory tier is low-specificity.** It fires on nearly every constituency because of the demo seed's uniform unspent ratio.
4. **Works data is demonstration scale.** 14 records, not 50,000. The spatial detector is O(n²) and would need grid or R-tree spatial indexing before running at national scale.
5. **No authentication or access control.** In deployment this would sit behind the ministry's existing SSO with role-based access.
6. **No live portal integration.** Data is ingested from a published CSV. The REST API is *designed* to consume from e-SAKSHI and PFMS, but that connection is not built.

> **Why this section exists:** judges forgive an incomplete prototype. They do not forgive a team
> that overstates what it built. Raising a limitation yourself reads as engineering maturity —
> exactly what a ministry wants in an audit tool.

---

## 🎙️ 7. Your 1-Minute Opening Pitch Script

> *"Respected judges, under the Member of Parliament Local Area Development Scheme, the central government releases thousands of crores every year to develop local schools, roads, and drinking water facilities.*
>
> *However, because those works are audited manually across 543 constituencies, four problems routinely go unnoticed for years: **duplicate ghost assets**, **contractor cartels**, **inflated billing**, and **stagnant unspent funds**.*
>
> *We built **NirmanDrishti** — an automated SQL and analytics surveillance platform. It ingests the official MoSPI allocation dataset for all 543 constituencies, then runs four detection engines: **Haversine GPS distance** for duplicate assets, a **NetworkX co-bidding graph** for cartels, **PWD Schedule of Rates** comparison with statistical outlier testing for inflated cost, and **temporal queries** for stalled funds.*
>
> *On our current dataset it raises **six confirmed findings** — including two borewells forty-five metres apart, and a village road sanctioned at 3.27 times the official ceiling.*
>
> *Every finding stores its own arithmetic, because in a corruption inquiry an alert an officer cannot recompute is an alert nobody can act on. Thank you."*

---

## 🎯 8. Top 10 Jury Questions & Your Answers

| Question from Judge | Your Clear, Confident Answer |
| :--- | :--- |
| **Q1: "Why SQL instead of NoSQL?"** | *"MPLADS data is deeply relational: an MP recommends a Work, a Work has Tenders, Tenders have Bids from Contractors. SQL guarantees foreign-key integrity and fast indexed joins. Concretely, cartel detection is only possible because bids join to both tenders and contractors — in a document store we would be reimplementing joins by hand."* |
| **Q2: "Why SQLite and not PostgreSQL?"** | *"For a prototype it needs no server, so the whole system runs with one command. The schema is standard SQL and the queries are portable — moving to PostgreSQL means changing the connection layer in `database.py`, not the detectors. For national deployment you would want Postgres with PostGIS for the spatial work."* |
| **Q3: "What if a contractor shifts the coordinates by 50 metres?"** | *"Our radius is 100 metres, so a 50-metre shift is still caught. Push it further and the fraud gets harder — the asset has to be plausibly in a different location, which makes physical verification easier. And evading one detector does not evade the others; the same work is still checked on cost and on bidding."* |
| **Q4: "How does the cartel detection work?"** | *"We build a bipartite graph in NetworkX — contractors on one side, tenders on the other, bids as edges. For each pair of contractors we count shared tenders as an edge weight. Above the threshold we flag the relationship. In our data, three contractors each won exactly one of three tenders while the other two bid marginally higher — textbook rotation."* |
| **Q5: "Isn't co-bidding normal? Contractors in one district naturally compete."** | *"Correct — which is why this is a flag for investigation, not a conviction. Co-bidding frequency alone is weak evidence; combined with rotating wins and razor-thin margins it is worth a human looking. A stronger version would weight the margin between bids, which we have not built yet."* |
| **Q6: "Why not use Deep Learning or a neural network?"** | *"Three reasons. There is no labelled corpus of confirmed MPLADS fraud to train on. A black-box score saying 'this project is 0.87 suspicious' is not admissible reasoning in a departmental inquiry. And with our current dataset size, any model would be fitting noise. Rules encode what auditors already know; ML would be needed for patterns nobody has articulated yet."* |
| **Q7: "What is a Z-score, and why use it here?"** | *"It measures how many standard deviations a value sits from the mean of the population. We flag above 2.5. Its value is that it catches inflated costs in categories where the PWD rate table is missing or outdated — the ceiling check needs a benchmark, the Z-score does not."* |
| **Q8: "Can this scale to all 543 constituencies and 50,000 works?"** | *"The constituency layer already runs at full national scale — all 543 are loaded, and a complete audit takes about 110 milliseconds. The works layer is at demonstration scale. Honestly: our spatial detector is O(n²) and would need spatial bucketing — grid or R-tree indexing — before 50,000 works. That is a solved problem, but we have not implemented it yet."* |
| **Q9: "Where is the AI in this?"** | *"It is rule-based and statistical, and that is a deliberate choice. Every alert we raise stores its own arithmetic so an officer can verify it independently. The system is built for evidentiary defensibility, not benchmark accuracy. Where machine learning would genuinely add value is detecting patterns we have not written rules for — and that is the natural next layer, on top of this evidence base rather than instead of it."* |
| **Q10: "What happens when an anomaly is detected?"** | *"It is written to the `anomalies` table with a severity level, a case reference, and its mathematical evidence, then appears as a coloured pin on the GIS map and in the triage feed. The schema already carries an Open / Under Investigation / Resolved / Dismissed workflow field. Routing those alerts to the District Nodal Officer and the MoSPI vigilance cell is the deployment step we have designed for but not yet built."* |

---

## 📁 9. Project Layout

```
nirmandrishti/
├── run.py                      one-click launcher
├── requirements.txt            fastapi, uvicorn, networkx
├── README.md                   technical documentation
├── EXPLAINER.md                this file
├── data/
│   └── mp_allocations.csv      official MoSPI dataset (543 MPs)
├── backend/
│   ├── config.py               every threshold, one file
│   ├── database.py             schema, connections, indexes
│   ├── main.py                 FastAPI app and endpoints
│   ├── seed_data.py            seeding orchestrator
│   ├── ingest/portal_csv.py    REAL government data
│   ├── seed/demo_scenarios.py  SYNTHETIC fraud fixtures
│   └── detectors/              the four engines
└── frontend/                   dashboard (no build step)
```
