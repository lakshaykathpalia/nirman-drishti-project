"""
Fund Stagnation & Project Inefficiency Tracker
Author: NirmanDrishti SIH Team
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection
import config

def run_stagnation_detection(idle_days_threshold=None, unspent_balance_threshold_cr=None):
    """Detects stalled projects and idle constituency funds."""
    if idle_days_threshold is None:
        idle_days_threshold = config.STAGNATION_IDLE_DAYS
    if unspent_balance_threshold_cr is None:
        unspent_balance_threshold_cr = config.IDLE_FUNDS_THRESHOLD_CR

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT work_id, work_name, constituency_id, sanctioned_amount_lakhs, sanction_date, completion_percent, location_name
    FROM works
    WHERE completion_percent < ?;
    """, (config.STAGNATION_MAX_COMPLETION_PERCENT,))
    stalled_works = cursor.fetchall()

    anomalies_found = []
    today = datetime.now().date()

    for w in stalled_works:
        s_date = datetime.strptime(w['sanction_date'], "%Y-%m-%d").date()
        days_passed = (today - s_date).days

        if days_passed >= idle_days_threshold:
            title = f"Project Stagnation Alert ({days_passed} Days Idle)"
            desc = (f"Project '{w['work_name']}' in {w['location_name']} sanctioned on {w['sanction_date']} "
                    f"has only reached {w['completion_percent']}% progress over {days_passed} days.")
            math_proof = f"Elapsed Days = {days_passed} >= {idle_days_threshold} Threshold. Progress = {w['completion_percent']}%."

            cursor.execute("""
            INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
            VALUES (?, 'FUND_STAGNATION', 'HIGH', ?, ?, ?);
            """, (w['work_id'], title, desc, math_proof))

            anomalies_found.append({
                "work_id": w['work_id'],
                "days_idle": days_passed,
                "completion_pct": w['completion_percent'],
                "proof": math_proof
            })

    # Both conditions must hold: a materially large balance, and a large share
    # of the allocation. Either alone flags most of the country.
    cursor.execute("""
    SELECT constituency_id, name, state, total_allocated_cr, unspent_balance_cr
    FROM constituencies
    WHERE unspent_balance_cr >= ?
      AND total_allocated_cr > 0
      AND (unspent_balance_cr / total_allocated_cr) >= ?;
    """, (unspent_balance_threshold_cr, config.IDLE_FUNDS_MIN_UNSPENT_RATIO))
    idle_constituencies = cursor.fetchall()

    for c in idle_constituencies:
        title = f"High Unspent Fund Accumulation: {c['name']} (Rs {c['unspent_balance_cr']:.2f} Cr)"
        desc = f"Constituency '{c['name']}' ({c['state']}) has Rs {c['unspent_balance_cr']:.2f} Cr unspent out of Rs {c['total_allocated_cr']:.2f} Cr allocated."
        math_proof = (f"Unspent Ratio: {(c['unspent_balance_cr'] / c['total_allocated_cr']) * 100:.1f}% "
                      f">= {config.IDLE_FUNDS_MIN_UNSPENT_RATIO * 100:.0f}% threshold, "
                      f"and Rs {c['unspent_balance_cr']:.2f} Cr >= Rs {unspent_balance_threshold_cr:.2f} Cr floor.")

        cursor.execute("""
        INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
        VALUES (NULL, 'IDLE_FUNDS', 'MEDIUM', ?, ?, ?);
        """, (title, desc, math_proof))

    conn.commit()
    conn.close()
    return anomalies_found

if __name__ == "__main__":
    stagnant = run_stagnation_detection()
    print(f"[*] Stagnation Tracker Found {len(stagnant)} stagnant cases.")
