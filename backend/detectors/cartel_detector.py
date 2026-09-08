"""
Contractor Cartel & Bid-Rigging Collusion Detector
Author: NirmanDrishti SIH Team
"""

import sys
import os
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection
import config

def run_cartel_detection(min_shared_tenders=None):
    """Detects collusive bidding rings among contractors."""
    if min_shared_tenders is None:
        min_shared_tenders = config.CARTEL_MIN_SHARED_TENDERS

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT b.tender_id, b.contractor_id, c.company_name, b.bid_amount_lakhs, b.is_winning_bid, t.work_id
    FROM bids b
    JOIN contractors c ON b.contractor_id = c.contractor_id
    JOIN tenders t ON b.tender_id = t.tender_id;
    """)
    bids_data = cursor.fetchall()

    if not bids_data:
        conn.close()
        return []

    tender_contractors = {}
    contractor_tenders = {}
    contractor_names = {}
    contractor_wins = {}

    for row in bids_data:
        t_id = row['tender_id']
        c_id = row['contractor_id']
        contractor_names[c_id] = row['company_name']

        if t_id not in tender_contractors:
            tender_contractors[t_id] = []
        tender_contractors[t_id].append(c_id)

        # Per-contractor tender sets, needed for the Jaccard overlap below.
        contractor_tenders.setdefault(c_id, set()).add(t_id)

        if row['is_winning_bid'] == 1:
            contractor_wins[c_id] = contractor_wins.get(c_id, 0) + 1

    G = nx.Graph()
    for contractors in tender_contractors.values():
        for i in range(len(contractors)):
            for j in range(i + 1, len(contractors)):
                c1, c2 = contractors[i], contractors[j]
                if G.has_edge(c1, c2):
                    G[c1][c2]['weight'] += 1
                else:
                    G.add_edge(c1, c2, weight=1)

    anomalies_found = []
    suspicious_edges = [(u, v, d['weight']) for u, v, d in G.edges(data=True) if d['weight'] >= min_shared_tenders]

    for u, v, weight in suspicious_edges:
        name_u = contractor_names.get(u, u)
        name_v = contractor_names.get(v, v)
        
        # Jaccard index: shared tenders over the union of both bidding histories.
        # 100% means neither contractor ever bid on a tender without the other.
        set_u = contractor_tenders.get(u, set())
        set_v = contractor_tenders.get(v, set())
        union = len(set_u | set_v)
        jaccard = (len(set_u & set_v) / union * 100.0) if union else 0.0

        title = f"Collusive Bidding Relationship ({u} & {v})"
        desc = (f"Contractors '{name_u}' and '{name_v}' have co-bid in {weight} different tenders together, "
                f"which is {jaccard:.0f}% of every tender either of them bid on. "
                f"This co-bidding pattern warrants review for cover bidding.")
        math_proof = (f"Co-Bidding Frequency W({u}, {v}) = {weight} tenders >= {min_shared_tenders} threshold. "
                      f"Jaccard Index |A intersect B| / |A union B| = {len(set_u & set_v)}/{union} = {jaccard:.1f}%.")

        cursor.execute("UPDATE contractors SET risk_score = 0.85 WHERE contractor_id IN (?, ?);", (u, v))

        cursor.execute("""
        INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
        VALUES (?, 'CARTEL_BID_RIGGING', 'HIGH', ?, ?, ?);
        """, ('WRK-PAT-01', title, desc, math_proof))

        anomalies_found.append({
            "contractor_1": name_u,
            "contractor_2": name_v,
            "shared_tenders": weight,
            "proof": math_proof
        })

    conn.commit()
    conn.close()
    return anomalies_found

if __name__ == "__main__":
    cartels = run_cartel_detection()
    print(f"[*] Cartel Detector Found {len(cartels)} suspicious bidding relationships.")
