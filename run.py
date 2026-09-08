"""
NirmanDrishti One-Click Launcher
Author: NirmanDrishti Team (SIH26102)

Usage:
  python run.py
"""

import os
import sys
import webbrowser
import time

# Windows consoles default to cp1252, which cannot encode the emoji below.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("=" * 70)
    print("🛡️  NIRMAN-DRISHTI: AI & SQL MPLADS INTEGRITY PLATFORM (SIH26102)")
    print("=" * 70)

    # Base paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")

    # Add backend to sys.path
    sys.path.insert(0, backend_dir)

    print("\n[1/3] Initializing SQLite Database & Seeding Real-World Dataset...")
    import config
    from database import init_db
    from seed_data import seed_database
    from main import trigger_all_audits

    init_db()
    seed_database()

    print("\n[2/3] Running All 4 Python & SQL Anomaly Detectors...")
    results = trigger_all_audits()
    print(f"      📍 Spatial Duplicates Detected: {results['spatial_duplicates']}")
    print(f"      🕸️  Cartel Rings Detected:     {results['cartel_rings']}")
    print(f"      💰 Price Inflations Detected:  {results['price_inflations']}")
    print(f"      ⏳ Stagnant Projects Tracked:  {results['stagnant_works']}")

    print("\n[3/3] Starting NirmanDrishti Web GIS Dashboard...")
    url = f"http://localhost:{config.SERVER_PORT}"
    print("      👉 URL: " + url)
    print("      Press Ctrl+C to stop the server.\n")

    # Auto-open browser after 1 second
    import threading
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)
    threading.Thread(target=open_browser).start()

    # Run Uvicorn
    import uvicorn
    uvicorn.run("main:app", app_dir=backend_dir, host=config.SERVER_HOST, port=config.SERVER_PORT, log_level="info")

if __name__ == "__main__":
    main()
