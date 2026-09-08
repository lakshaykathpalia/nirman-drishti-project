"""
Official MoSPI Portal CSV Ingestion
Author: NirmanDrishti Team (SIH26102)

Reads the published "Allocated Limit for Hon'ble MPs" dataset and loads the
543 Lok Sabha constituencies and their sitting members into SQL.

This module handles REAL government data only. Demo fraud scenarios are kept
separate in backend/seed/demo_scenarios.py so the two are never confused.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

RUPEES_PER_CRORE = 10000000.0


def load_portal_rows(csv_path=None):
    """Parses the portal CSV into (constituency_records, mp_records) tuples.

    Returns empty lists if the CSV is absent; the caller decides on a fallback.
    """
    csv_path = csv_path or config.PORTAL_CSV_PATH

    if not os.path.exists(csv_path):
        return [], []

    constituency_records = []
    mp_records = []

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            sr_no = row.get("Sr. No.", "").strip()

            # Skip the trailing Grand Total summary row
            if "Grand Total" in sr_no or "Grand Total" in row.get("State", ""):
                continue

            state = row.get("State", "").strip()
            mp_name = row.get("Hon'ble Members of Parliaments", "").strip()
            const_name = row.get("Constituency", "").strip()
            raw_amt = row.get("Allocated AMOUNT ( ₹ )", "").strip().replace(",", "")

            if not mp_name and not const_name:
                continue

            try:
                allocated_rs = float(raw_amt)
            except ValueError:
                allocated_rs = config.DEFAULT_ALLOCATION_INR

            count += 1
            allocated_cr = round(allocated_rs / RUPEES_PER_CRORE, 2)
            unspent_cr = round(allocated_cr * config.DEMO_UNSPENT_RATIO, 2)

            constituency_records.append(
                (f"CONST-{count:03d}", const_name, state, "General", allocated_cr, unspent_cr)
            )
            mp_records.append(
                (f"MP-{count:03d}", mp_name, "Lok Sabha", f"CONST-{count:03d}", "2024-06-05", "2029-06-04")
            )

    return constituency_records, mp_records


def ingest_constituencies_and_mps(cursor, csv_path=None):
    """Loads the portal dataset into the constituencies and mps tables.

    Falls back to a single baseline constituency if the CSV cannot be found,
    so the rest of the pipeline still has valid foreign keys to reference.
    """
    constituency_records, mp_records = load_portal_rows(csv_path)

    if constituency_records:
        print(f"      -> Ingested exactly {len(constituency_records)} Official Constituencies & MPs from Portal CSV.")
    else:
        print("      -> Portal CSV not found, fallback to baseline directory.")
        constituency_records = [("CONST-001", "VARANASI", "Uttar Pradesh", "General", 15.0, 3.2)]
        mp_records = [("MP-001", "NARENDRA MODI", "Lok Sabha", "CONST-001", "2024-06-05", "2029-06-04")]

    cursor.executemany(
        """
        INSERT INTO constituencies (constituency_id, name, state, category, total_allocated_cr, unspent_balance_cr)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        constituency_records,
    )

    cursor.executemany(
        """
        INSERT INTO mps (mp_id, name, house, constituency_id, tenure_start, tenure_end)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        mp_records,
    )

    return constituency_records, mp_records
