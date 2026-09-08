"""
NirmanDrishti Database Seeding Orchestrator
Author: NirmanDrishti Team (SIH26102)

Coordinates two clearly separated sources:
  1. backend/ingest/portal_csv.py    -> REAL MoSPI portal data (543 MPs)
  2. backend/seed/demo_scenarios.py  -> SYNTHETIC fraud fixtures for the demo
"""

import os
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, init_db
from ingest.portal_csv import ingest_constituencies_and_mps
from seed import demo_scenarios

# Tables cleared in dependency order (children before parents)
TABLES_TO_CLEAR = [
    'anomalies', 'bids', 'tenders', 'works',
    'pwd_benchmarks', 'contractors', 'mps', 'constituencies',
]


def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    for table in TABLES_TO_CLEAR:
        cursor.execute(f"DELETE FROM {table};")

    print("[1/5] Ingesting Official MoSPI Portal CSV (543 Constituencies & MPs)...")
    constituency_records, mp_records = ingest_constituencies_and_mps(cursor)

    print("[2/5] Seeding PWD Benchmark Schedule of Rates...")
    cursor.executemany(
        """
        INSERT INTO pwd_benchmarks (category, unit, avg_rate_inr, max_acceptable_rate_inr, description)
        VALUES (?, ?, ?, ?, ?);
        """,
        demo_scenarios.PWD_BENCHMARKS,
    )

    print("[3/5] Seeding Contractors...")
    cursor.executemany(
        """
        INSERT INTO contractors (contractor_id, company_name, pan_number, owner_name, registered_district, blacklisted, risk_score)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        demo_scenarios.CONTRACTORS,
    )

    def get_c_id(name_fragment):
        r = cursor.execute(
            "SELECT constituency_id, name FROM constituencies WHERE name LIKE ? LIMIT 1;",
            (f"%{name_fragment}%",),
        ).fetchone()
        return r['constituency_id'] if r else constituency_records[0][0]

    def get_mp_id(c_id):
        r = cursor.execute(
            "SELECT mp_id FROM mps WHERE constituency_id = ? LIMIT 1;", (c_id,)
        ).fetchone()
        return r['mp_id'] if r else mp_records[0][0]

    print("[4/5] Linking Audited Projects & Injected Fraud Cases to Official Constituencies...")
    works = demo_scenarios.build_works(
        cid_var=get_c_id("VARANASI"),
        cid_del=get_c_id("NEW DELHI"),
        cid_blr=get_c_id("BANGALORE SOUTH") or get_c_id("BANGALORE"),
        cid_pat=get_c_id("PATNA SAHIB") or get_c_id("PATNA"),
        cid_jpr=get_c_id("JAIPUR RURAL") or get_c_id("JAIPUR"),
        cid_wyd=get_c_id("WAYANAD"),
        get_mp_id=get_mp_id,
    )

    cursor.executemany(
        """
        INSERT INTO works (work_id, constituency_id, mp_id, work_name, work_category, sanctioned_amount_lakhs, disbursed_amount_lakhs,
                           status, sanction_date, last_inspection_date, latitude, longitude, location_name, implementing_agency,
                           contractor_id, completion_percent, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        works,
    )

    print("[5/5] Seeding Tenders & Cartel Bidding...")
    cursor.executemany(
        """
        INSERT INTO tenders (tender_id, work_id, estimated_cost_lakhs, tender_publish_date, winning_contractor_id, winning_bid_lakhs, status)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        demo_scenarios.TENDERS,
    )

    cursor.executemany(
        """
        INSERT INTO bids (tender_id, contractor_id, bid_amount_lakhs, bid_date, is_winning_bid)
        VALUES (?, ?, ?, ?, ?);
        """,
        demo_scenarios.BIDS,
    )

    conn.commit()
    conn.close()
    print("[SUCCESS] Ingested Official 543 MPs Dataset + Seeded Live Fraud Scenarios.")


if __name__ == "__main__":
    seed_database()
