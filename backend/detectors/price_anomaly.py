"""
Price Inflation & Schedule of Rates (SoR) Anomaly Detector
Author: NirmanDrishti SIH Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection
import config

def run_price_anomaly_detection(inflation_threshold_multiplier=None):
    """Scans for inflated work estimates against standard PWD schedules."""
    if inflation_threshold_multiplier is None:
        inflation_threshold_multiplier = config.PRICE_INFLATION_MULTIPLIER

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT w.work_id, w.work_name, w.work_category, w.sanctioned_amount_lakhs, w.location_name,
           p.avg_rate_inr, p.max_acceptable_rate_inr, p.unit
    FROM works w
    JOIN pwd_benchmarks p ON w.work_category = p.category;
    """)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return []

    anomalies_found = []

    # 1. Rule-Based PWD Schedule of Rates Ceiling Check
    for r in rows:
        sanctioned = r['sanctioned_amount_lakhs']
        max_acceptable = r['max_acceptable_rate_inr']
        ratio = sanctioned / max_acceptable

        if ratio >= inflation_threshold_multiplier:
            pct_inflated = (ratio - 1.0) * 100.0
            title = f"Severe Cost Inflation ({r['work_category']})"
            desc = (f"Project '{r['work_name']}' in {r['location_name']} sanctioned for Rs {sanctioned:.2f} Lakhs. "
                    f"PWD Maximum Benchmark is Rs {max_acceptable:.2f} Lakhs ({pct_inflated:.1f}% inflated).")
            math_proof = (f"Sanctioned = Rs {sanctioned}L, Max PWD Ceiling = Rs {max_acceptable}L. "
                          f"Price Ratio = {ratio:.2f}x (Threshold is {inflation_threshold_multiplier}x).")

            cursor.execute("""
            INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
            VALUES (?, 'PRICE_INFLATION', 'CRITICAL', ?, ?, ?);
            """, (r['work_id'], title, desc, math_proof))

            anomalies_found.append({
                "work_id": r['work_id'],
                "sanctioned_lakhs": sanctioned,
                "benchmark_lakhs": max_acceptable,
                "inflation_pct": round(pct_inflated, 1),
                "proof": math_proof
            })

    # 2. Statistical Z-Score / ML Outlier Check
    costs = [r['sanctioned_amount_lakhs'] for r in rows]
    if len(costs) >= 4:
        mean_cost = sum(costs) / len(costs)
        variance = sum((x - mean_cost) ** 2 for x in costs) / len(costs)
        std_dev = max(0.001, variance ** 0.5)

        for r in rows:
            z_score = (r['sanctioned_amount_lakhs'] - mean_cost) / std_dev
            if z_score > config.PRICE_OUTLIER_Z_SCORE: # Extreme statistical outlier
                # Check if not already added
                if not any(a['work_id'] == r['work_id'] for a in anomalies_found):
                    title = f"Statistical Price Outlier (Z-Score {z_score:.2f})"
                    desc = f"Project '{r['work_name']}' is statistical outlier with cost Rs {r['sanctioned_amount_lakhs']}L."
                    math_proof = f"Z-Score = (x - mu)/sigma = ({r['sanctioned_amount_lakhs']} - {mean_cost:.2f})/{std_dev:.2f} = {z_score:.2f} > {config.PRICE_OUTLIER_Z_SCORE}"
                    cursor.execute("""
                    INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
                    VALUES (?, 'PRICE_INFLATION', 'HIGH', ?, ?, ?);
                    """, (r['work_id'], title, desc, math_proof))

    conn.commit()
    conn.close()
    return anomalies_found

if __name__ == "__main__":
    price_anomalies = run_price_anomaly_detection()
    print(f"[*] Price Anomaly Detector Found {len(price_anomalies)} price-gouging cases.")
