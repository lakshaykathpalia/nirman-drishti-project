"""
NirmanDrishti Core API Server (FastAPI)
Author: NirmanDrishti AI & GovTech Team (SIH26102)
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from database import get_connection, init_db
from seed_data import seed_database
from detectors.spatial_detector import run_spatial_detection
from detectors.cartel_detector import run_cartel_detection
from detectors.price_anomaly import run_price_anomaly_detection
from detectors.stagnation_detector import run_stagnation_detection

app = FastAPI(
    title="NirmanDrishti MPLADS Audit & Integrity API",
    description="Automated AI and SQL Surveillance Platform for MoSPI (SIH26102)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def revalidate_frontend(request, call_next):
    """Force the browser to revalidate the dashboard on every load.

    Without this the browser heuristically caches app.js and style.css, so a
    change to the frontend silently does not appear until a hard refresh —
    which is a bad surprise mid-demo. The ETag still makes revalidation cheap:
    unchanged files come back as an empty 304.
    """
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


FRONTEND_DIR = config.FRONTEND_DIR

@app.on_event("startup")
def startup_event():
    init_db()
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM works").fetchone()[0]
    conn.close()
    if count == 0:
        seed_database()
        trigger_all_audits()

def trigger_all_audits():
    conn = get_connection()
    conn.execute("DELETE FROM anomalies;")
    conn.commit()
    conn.close()

    # Thresholds come from backend/config.py
    sp_res = run_spatial_detection()
    ct_res = run_cartel_detection()
    pr_res = run_price_anomaly_detection()
    st_res = run_stagnation_detection()
    return {
        "spatial_duplicates": len(sp_res),
        "cartel_rings": len(ct_res),
        "price_inflations": len(pr_res),
        "stagnant_works": len(st_res)
    }

@app.get("/api/stats")
def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    total_works = cursor.execute("SELECT COUNT(*) FROM works;").fetchone()[0]
    total_mps = cursor.execute("SELECT COUNT(*) FROM mps;").fetchone()[0]
    total_allocated_cr = cursor.execute("SELECT SUM(total_allocated_cr) FROM constituencies;").fetchone()[0] or 0.0
    total_sanctioned = cursor.execute("SELECT SUM(sanctioned_amount_lakhs) FROM works;").fetchone()[0] or 0.0
    total_anomalies = cursor.execute("SELECT COUNT(*) FROM anomalies;").fetchone()[0]
    critical_flags = cursor.execute("SELECT COUNT(*) FROM anomalies WHERE severity = 'CRITICAL';").fetchone()[0]
    
    # Sum each flagged work ONCE. Joining works to anomalies counts a work as
    # many times as it has findings, which silently inflates the headline figure
    # the moment any work trips two detectors.
    risk_funds = cursor.execute("""
    SELECT SUM(sanctioned_amount_lakhs)
    FROM works
    WHERE work_id IN (
        SELECT DISTINCT work_id FROM anomalies
        WHERE severity IN ('CRITICAL', 'HIGH') AND work_id IS NOT NULL
    );
    """).fetchone()[0] or 0.0

    conn.close()

    return {
        "total_works": total_works,
        "total_mps_registered": total_mps,
        "total_national_budget_cr": round(total_allocated_cr, 2),
        "total_sanctioned_cr": round(total_sanctioned / 100.0, 2),
        "total_anomalies_detected": total_anomalies,
        "critical_red_flags": critical_flags,
        "funds_at_risk_lakhs": round(risk_funds, 2),
        "dataset_source": "Official MoSPI / e-SAKSHI Portal (543 MPs Ingested)"
    }

@app.get("/api/mps")
def get_all_mps():
    """Returns directory of all 543 Hon'ble MPs and their official allocated budget from the portal CSV."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT m.mp_id, m.name as mp_name, m.house, c.name as constituency_name, c.state,
           c.total_allocated_cr, c.unspent_balance_cr,
           (SELECT COUNT(*) FROM works w WHERE w.mp_id = m.mp_id) as total_works_count
    FROM mps m
    JOIN constituencies c ON m.constituency_id = c.constituency_id
    ORDER BY c.state ASC, c.name ASC;
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/works")
def get_all_works():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT w.work_id, w.work_name, w.work_category, w.sanctioned_amount_lakhs, w.disbursed_amount_lakhs,
           w.status, w.sanction_date, w.latitude, w.longitude, w.location_name, w.completion_percent,
           w.risk_level, c.name as constituency_name, c.state, m.name as mp_name,
           (SELECT COUNT(*) FROM anomalies a WHERE a.work_id = w.work_id) as anomaly_count
    FROM works w
    JOIN constituencies c ON w.constituency_id = c.constituency_id
    JOIN mps m ON w.mp_id = m.mp_id
    ORDER BY anomaly_count DESC, w.sanction_date DESC;
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/anomalies")
def get_all_anomalies():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT a.anomaly_id, a.work_id, a.anomaly_type, a.severity, a.title, a.description,
           a.mathematical_evidence, a.detected_at, a.status,
           w.work_name, w.location_name, c.name as constituency_name
    FROM anomalies a
    LEFT JOIN works w ON a.work_id = w.work_id
    LEFT JOIN constituencies c ON w.constituency_id = c.constituency_id
    ORDER BY 
        CASE a.severity
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4
        END, a.detected_at DESC;
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/benchmarks")
def get_pwd_benchmarks():
    """PWD Schedule of Rates reference table, used by the dashboard to chart
    sanctioned cost against the official ceiling for each work category."""
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT category, unit, avg_rate_inr, max_acceptable_rate_inr, description FROM pwd_benchmarks;"
    ).fetchall()]
    conn.close()
    return rows

@app.get("/api/cartel-network")
def get_cartel_network_data():
    conn = get_connection()
    cursor = conn.cursor()

    contractors = [dict(r) for r in cursor.execute("SELECT contractor_id, company_name, registered_district, risk_score FROM contractors;").fetchall()]
    tenders = [dict(r) for r in cursor.execute("SELECT tender_id, estimated_cost_lakhs FROM tenders;").fetchall()]
    bids = [dict(r) for r in cursor.execute("SELECT tender_id, contractor_id, bid_amount_lakhs, is_winning_bid FROM bids;").fetchall()]
    conn.close()

    nodes = []
    for c in contractors:
        nodes.append({
            "id": c['contractor_id'],
            "label": c['company_name'],
            "type": "contractor",
            "risk": c['risk_score'],
            "district": c['registered_district']
        })
    for t in tenders:
        nodes.append({
            "id": t['tender_id'],
            "label": f"Tender {t['tender_id']}",
            "type": "tender",
            "cost": t['estimated_cost_lakhs']
        })

    links = []
    for b in bids:
        links.append({
            "source": b['contractor_id'],
            "target": b['tender_id'],
            "amount": b['bid_amount_lakhs'],
            "is_winner": bool(b['is_winning_bid'])
        })

    return {"nodes": nodes, "links": links}

@app.post("/api/trigger-audit")
def trigger_audit_endpoint():
    results = trigger_all_audits()
    return {"status": "success", "message": "Audit completed successfully", "results": results}

@app.post("/api/reset-data")
def reset_seed_data_endpoint():
    seed_database()
    trigger_all_audits()
    return {"status": "success", "message": "Database reset to benchmark state"}

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=True)
