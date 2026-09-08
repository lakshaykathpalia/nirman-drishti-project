"""
NirmanDrishti Central Configuration
Author: NirmanDrishti Team (SIH26102)

Every detector threshold and filesystem path lives here. Tuning the audit
sensitivity for a different district size is a single-file change.
"""

import os

# --- Paths -----------------------------------------------------------------

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

DB_PATH = os.path.join(BACKEND_DIR, "mplads.db")
PORTAL_CSV_PATH = os.path.join(DATA_DIR, "mp_allocations.csv")

# --- Server ----------------------------------------------------------------

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

# --- Detector 1: Spatial duplicates ----------------------------------------
# Two works of the same category, in the same constituency, closer than this
# great-circle distance are treated as a probable duplicate sanction.

SPATIAL_DUPLICATE_RADIUS_METERS = 100.0

# --- Detector 2: Contractor cartels ----------------------------------------
# Number of tenders two contractors must have co-bid on before the pairing is
# treated as a possible bid-rigging relationship.

CARTEL_MIN_SHARED_TENDERS = 2

# --- Detector 3: Price inflation -------------------------------------------
# A work is flagged when its sanctioned amount reaches this multiple of the
# PWD Schedule of Rates ceiling for its category.

PRICE_INFLATION_MULTIPLIER = 1.5

# Secondary statistical check: standard deviations above the mean cost at
# which a work is reported as an outlier.
PRICE_OUTLIER_Z_SCORE = 2.5

# --- Detector 4: Stagnation and idle funds ----------------------------------
# A work is stagnant when it has been sanctioned for at least this many days
# while remaining below the completion threshold.

STAGNATION_IDLE_DAYS = 180
STAGNATION_MAX_COMPLETION_PERCENT = 20

# Constituency-level unspent balance (in crore) that triggers an idle-funds
# alert. NOTE: the demo seed gives every constituency ~35% of its allocation
# as unspent, so at 2.0 this fires on essentially all 543 rows. See README.
IDLE_FUNDS_THRESHOLD_CR = 2.0

# --- Seed / ingestion defaults ---------------------------------------------

# Fallback allocation (rupees) when a portal CSV row has an unparseable amount.
DEFAULT_ALLOCATION_INR = 147000000.0

# Fraction of each constituency's allocation recorded as unspent in the demo seed.
DEMO_UNSPENT_RATIO = 0.35
