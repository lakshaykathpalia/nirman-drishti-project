"""
NirmanDrishti Database Engine (SQLite / SQL)
Author: NirmanDrishti AI & GovTech Team (SIH26102)
"""

import sqlite3
import os
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

DB_PATH = config.DB_PATH

def get_connection():
    """Returns a SQLite connection with row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes all database tables with proper relational constraints, types, and indexes."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Constituencies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS constituencies (
        constituency_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        total_allocated_cr REAL DEFAULT 5.0,
        unspent_balance_cr REAL DEFAULT 5.0
    );
    """)

    # 2. Members of Parliament (MPs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mps (
        mp_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        house TEXT NOT NULL CHECK(house IN ('Lok Sabha', 'Rajya Sabha')),
        constituency_id TEXT,
        tenure_start DATE,
        tenure_end DATE,
        FOREIGN KEY (constituency_id) REFERENCES constituencies(constituency_id)
    );
    """)

    # 3. Contractors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contractors (
        contractor_id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        pan_number TEXT UNIQUE,
        owner_name TEXT NOT NULL,
        registered_district TEXT NOT NULL,
        blacklisted INTEGER DEFAULT 0,
        risk_score REAL DEFAULT 0.0
    );
    """)

    # 4. Standard PWD Schedule of Rates (Benchmark Price Reference)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pwd_benchmarks (
        category TEXT PRIMARY KEY,
        unit TEXT NOT NULL,
        avg_rate_inr REAL NOT NULL,
        max_acceptable_rate_inr REAL NOT NULL,
        description TEXT
    );
    """)

    # 5. Works / Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS works (
        work_id TEXT PRIMARY KEY,
        constituency_id TEXT NOT NULL,
        mp_id TEXT NOT NULL,
        work_name TEXT NOT NULL,
        work_category TEXT NOT NULL,
        sanctioned_amount_lakhs REAL NOT NULL,
        disbursed_amount_lakhs REAL DEFAULT 0.0,
        status TEXT NOT NULL CHECK(status IN ('Sanctioned', 'In Progress', 'Completed', 'Delayed', 'Suspended')),
        sanction_date DATE NOT NULL,
        last_inspection_date DATE,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        location_name TEXT NOT NULL,
        implementing_agency TEXT NOT NULL,
        contractor_id TEXT,
        completion_percent INTEGER DEFAULT 0,
        risk_level TEXT DEFAULT 'Normal' CHECK(risk_level IN ('Normal', 'Medium', 'High', 'Critical')),
        FOREIGN KEY (constituency_id) REFERENCES constituencies(constituency_id),
        FOREIGN KEY (mp_id) REFERENCES mps(mp_id),
        FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id),
        FOREIGN KEY (work_category) REFERENCES pwd_benchmarks(category)
    );
    """)

    # 6. Tenders & Bidding Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        tender_id TEXT PRIMARY KEY,
        work_id TEXT NOT NULL,
        estimated_cost_lakhs REAL NOT NULL,
        tender_publish_date DATE NOT NULL,
        winning_contractor_id TEXT,
        winning_bid_lakhs REAL,
        status TEXT DEFAULT 'Awarded',
        FOREIGN KEY (work_id) REFERENCES works(work_id),
        FOREIGN KEY (winning_contractor_id) REFERENCES contractors(contractor_id)
    );
    """)

    # 7. Contractor Bids (For Cartel & Collusion Analysis)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bids (
        bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_id TEXT NOT NULL,
        contractor_id TEXT NOT NULL,
        bid_amount_lakhs REAL NOT NULL,
        bid_date DATE NOT NULL,
        is_winning_bid INTEGER DEFAULT 0,
        FOREIGN KEY (tender_id) REFERENCES tenders(tender_id),
        FOREIGN KEY (contractor_id) REFERENCES contractors(contractor_id)
    );
    """)

    # 8. Detected Anomalies / Audit Flags Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_id TEXT,
        anomaly_type TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        mathematical_evidence TEXT NOT NULL,
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'Under Investigation', 'Resolved', 'Dismissed')),
        FOREIGN KEY (work_id) REFERENCES works(work_id)
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_constituency ON works(constituency_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_geo ON works(latitude, longitude);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_category ON works(work_category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bids_tender ON bids(tender_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bids_contractor ON bids(contractor_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON anomalies(severity);")

    conn.commit()
    conn.close()
    print("[SUCCESS] NirmanDrishti SQL Database Schema initialized successfully.")

if __name__ == "__main__":
    init_db()
