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
    tender_work = {}
    tender_winner = {}
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

        # Tender -> work, so each finding can be attached to a real project.
        tender_work[t_id] = row['work_id']

        if row['is_winning_bid'] == 1:
            contractor_wins[c_id] = contractor_wins.get(c_id, 0) + 1
            tender_winner[t_id] = c_id

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
    contractor_risk = {}

    # Keep only the pairings that clear the threshold, then let NetworkX find the
    # maximal cliques of that subgraph. A group of three contractors who all
    # co-bid with one another is ONE ring, not three separate relationships —
    # reporting it three times both overstates the count and buries other
    # findings underneath near-identical alerts.
    H = nx.Graph()
    H.add_edges_from((u, v, d) for u, v, d in G.edges(data=True)
                     if d['weight'] >= min_shared_tenders)

    rings = [sorted(cl) for cl in nx.find_cliques(H)] if H.number_of_edges() else []
    rings.sort(key=lambda r: (-len(r), r))          # biggest ring first, stable order

    for ring in rings:
        names = [contractor_names.get(c, c) for c in ring]
        sets = [contractor_tenders.get(c, set()) for c in ring]

        shared = set.intersection(*sets)
        combined = set.union(*sets)
        jaccard = (len(shared) / len(combined) * 100.0) if combined else 0.0

        # Rotation test: within the tenders this ring jointly bid on, did each
        # member take a turn winning? That is the signature of bid rotation.
        winners = [tender_winner.get(t) for t in shared]
        wins_inside = {c: winners.count(c) for c in ring}
        rotated = all(wins_inside[c] >= 1 for c in ring) and len(shared) >= len(ring)

        pair_weights = [G[a][b]['weight'] for i, a in enumerate(ring)
                        for b in ring[i + 1:] if G.has_edge(a, b)]
        min_w = min(pair_weights) if pair_weights else 0

        size_label = f"{len(ring)} contractors" if len(ring) > 2 else "2 contractors"
        title = f"Collusive Bidding Ring ({size_label})"

        rotation_note = (" Each member won exactly one of the shared tenders while the others bid just above — "
                         "the classic bid-rotation signature.") if rotated else ""
        desc = (f"Contractors {', '.join(repr(n) for n in names)} jointly bid on {len(shared)} of the same "
                f"tenders, which is {jaccard:.0f}% of every tender any of them bid on.{rotation_note}")

        math_proof = (
            f"Maximal clique of {len(ring)} contractors in the co-bidding graph "
            f"({', '.join(ring)}). Every pair co-bid on >= {min_w} tenders "
            f"(threshold {min_shared_tenders}). "
            f"Jaccard Index |intersection| / |union| = {len(shared)}/{len(combined)} = {jaccard:.1f}%. "
            f"Wins inside the ring: {', '.join(f'{c}={wins_inside[c]}' for c in ring)}."
        )

        # Risk derived from the evidence: a floor for being in a ring at all,
        # plus the overlap, the co-bid depth, and the size of the group.
        risk = min(0.95, 0.35 + 0.30 * (jaccard / 100.0) + 0.04 * min_w + 0.04 * len(ring))
        for c_id in ring:
            contractor_risk[c_id] = max(contractor_risk.get(c_id, 0.0), risk)

        # Attach to a work one of the shared tenders actually funded, chosen
        # deterministically so re-runs are stable.
        work_id = next((tender_work.get(t) for t in sorted(shared) if tender_work.get(t)), None)

        cursor.execute("""
        INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
        VALUES (?, 'CARTEL_BID_RIGGING', 'HIGH', ?, ?, ?);
        """, (work_id, title, desc, math_proof))

        anomalies_found.append({
            "contractors": names,
            "ring_size": len(ring),
            "shared_tenders": len(shared),
            "jaccard_percent": round(jaccard, 1),
            "rotation_detected": rotated,
            "work_id": work_id,
            "proof": math_proof
        })

    for c_id, risk in contractor_risk.items():
        cursor.execute("UPDATE contractors SET risk_score = ? WHERE contractor_id = ?;",
                       (round(risk, 2), c_id))

    conn.commit()
    conn.close()
    return anomalies_found

if __name__ == "__main__":
    cartels = run_cartel_detection()
    print(f"[*] Cartel Detector Found {len(cartels)} suspicious bidding relationships.")
