import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detectors.spatial_detector import run_spatial_detection
from detectors.cartel_detector import run_cartel_detection
from detectors.price_anomaly import run_price_anomaly_detection
from detectors.stagnation_detector import run_stagnation_detection

print("[1/4] Running Spatial Detector...")
sp = run_spatial_detection()
print(f"      -> Found {len(sp)} spatial duplicate anomalies.")

print("[2/4] Running Cartel Detector...")
ct = run_cartel_detection()
print(f"      -> Found {len(ct)} cartel relationships.")

print("[3/4] Running Price Anomaly Detector...")
pr = run_price_anomaly_detection()
print(f"      -> Found {len(pr)} price inflation anomalies.")

print("[4/4] Running Stagnation Tracker...")
st = run_stagnation_detection()
print(f"      -> Found {len(st)} stagnant fund cases.")

print("\nAll 4 Detectors executed perfectly!")
