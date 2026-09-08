"""
Spatial Duplicate & Ghost Project Detector
Author: NirmanDrishti SIH Team
"""

import math
import sys
import os

# Robust path handling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection
import config

def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Computes great-circle distance between two GPS points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def run_spatial_detection(distance_threshold_meters=None):
    """Scans the database and detects spatial duplicate sanctions."""
    if distance_threshold_meters is None:
        distance_threshold_meters = config.SPATIAL_DUPLICATE_RADIUS_METERS

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT work_id, work_name, work_category, constituency_id, latitude, longitude, sanctioned_amount_lakhs, location_name
    FROM works
    ORDER BY constituency_id, work_category;
    """)
    works = cursor.fetchall()
    
    anomalies_found = []

    for i in range(len(works)):
        for j in range(i + 1, len(works)):
            w1 = works[i]
            w2 = works[j]

            if w1['work_category'] == w2['work_category'] and w1['constituency_id'] == w2['constituency_id']:
                dist = haversine_distance_meters(w1['latitude'], w1['longitude'], w2['latitude'], w2['longitude'])
                
                if dist <= distance_threshold_meters:
                    title = f"High-Density Duplicate Sanction ({w1['work_category']})"
                    desc = (f"Project '{w1['work_name']}' (Rs {w1['sanctioned_amount_lakhs']}L) and "
                            f"Project '{w2['work_name']}' (Rs {w2['sanctioned_amount_lakhs']}L) are located only "
                            f"{dist:.1f} meters apart in {w1['location_name']}.")
                    math_proof = (f"Haversine GPS Distance: {dist:.2f}m <= {distance_threshold_meters}m threshold. "
                                  f"P1:({w1['latitude']:.4f}, {w1['longitude']:.4f}) vs P2:({w2['latitude']:.4f}, {w2['longitude']:.4f}).")

                    cursor.execute("""
                    INSERT INTO anomalies (work_id, anomaly_type, severity, title, description, mathematical_evidence)
                    VALUES (?, 'SPATIAL_DUPLICATE', 'CRITICAL', ?, ?, ?);
                    """, (w1['work_id'], title, desc, math_proof))

                    anomalies_found.append({
                        "work_1": w1['work_id'],
                        "work_2": w2['work_id'],
                        "distance_m": round(dist, 2),
                        "description": desc
                    })

    conn.commit()
    conn.close()
    return anomalies_found

if __name__ == "__main__":
    results = run_spatial_detection()
    print(f"[*] Spatial Detector Found {len(results)} duplicate anomalies.")
