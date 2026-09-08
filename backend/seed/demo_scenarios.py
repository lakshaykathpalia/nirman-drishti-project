"""
Demo Fraud Scenario Fixtures
Author: NirmanDrishti Team (SIH26102)

SYNTHETIC DATA ONLY. These rows are hand-authored so that each of the four
detectors has a known case to find during a demo:

  * WRK-VAR-03 / WRK-VAR-04 -> two borewells ~45 m apart  (spatial duplicate)
  * WRK-JPR-01              -> Rs 54L road, PWD ceiling Rs 16.5L (price inflation)
  * WRK-BLR-01             -> 5% complete after 300+ days (stagnation)
  * CONTR-05/06/07          -> rotating wins across 3 tenders (cartel)

Real government data is ingested separately in backend/ingest/portal_csv.py.
Nothing in this file should ever be presented as official MoSPI data.
"""

# --- PWD Schedule of Rates benchmarks --------------------------------------

PWD_BENCHMARKS = [
    ('Borewell / Handpump', 'Per Unit', 0.75, 1.20, 'Drilling and installation of submersible pump & solar mini-tank (Rs 0.75 - 1.20 Lakhs)'),
    ('Community Hall / Bhavan', 'Per 1000 sqft', 18.00, 25.00, 'RCC Community Building with basic sanitary facilities (Rs 18.00 - 25.00 Lakhs)'),
    ('Concrete Village Road', 'Per KM', 12.00, 16.50, 'CC Pavement 3.75m width standard rural road (Rs 12.00 - 16.50 Lakhs/km)'),
    ('High-Mast Solar Light', 'Per Unit', 1.80, 2.50, '9-meter high-mast LED solar lighting system (Rs 1.80 - 2.50 Lakhs)'),
    ('School Classroom / Lab', 'Per Room', 6.50, 9.00, 'Smart classroom construction with electrification (Rs 6.50 - 9.00 Lakhs)'),
    ('Public Health Dispensary', 'Per Unit', 35.00, 48.00, 'Primary sub-centre clinic building (Rs 35.00 - 48.00 Lakhs)'),
]

# --- Contractors ------------------------------------------------------------

CONTRACTORS = [
    ('CONTR-01', 'Purvanchal Infra & Works Ltd', 'AABCP1234F', 'Ramesh Yadav', 'Varanasi', 0, 0.1),
    ('CONTR-02', 'Ganga Construction & Engineering', 'BBECP5678G', 'Sunil Tiwari', 'Varanasi', 0, 0.2),
    ('CONTR-03', 'Apex Urban Developers', 'CCDEP9012H', 'Vikram Malhotra', 'New Delhi', 0, 0.05),
    ('CONTR-04', 'Karnataka Civil Builders', 'DDEMP3456I', 'Suresh Gowda', 'Bengaluru', 0, 0.1),
    ('CONTR-05', 'Magadh Buildcon Pvt Ltd', 'EEFMP7890J', 'Anil Singh', 'Patna', 0, 0.85),
    ('CONTR-06', 'Patliputra Engineering Works', 'FFGMP1234K', 'Pankaj Kumar', 'Patna', 0, 0.82),
    ('CONTR-07', 'Maa Sharda Infra Associates', 'GGHMP5678L', 'Sanjay Verma', 'Patna', 0, 0.88),
    ('CONTR-08', 'Thar Mega Structures', 'HHIMP9012M', 'Mahipal Singh', 'Jaipur', 0, 0.92),
    ('CONTR-09', 'Malabar Infrastructure Hub', 'IIJMP3456N', 'Manoj Kurian', 'Wayanad', 0, 0.1),
]

# --- Tenders ----------------------------------------------------------------

TENDERS = [
    ('TND-PAT-01', 'WRK-PAT-01', 24.0, '2024-12-01', 'CONTR-05', 23.50, 'Awarded'),
    ('TND-PAT-02', 'WRK-PAT-02', 16.0, '2025-01-10', 'CONTR-06', 15.80, 'Awarded'),
    ('TND-PAT-03', 'WRK-PAT-03', 45.0, '2025-02-15', 'CONTR-07', 44.00, 'Awarded'),
    ('TND-JPR-01', 'WRK-JPR-01', 55.0, '2025-02-01', 'CONTR-08', 54.00, 'Awarded'),
]

# --- Bids: CONTR-05/06/07 rotate wins across the three Patna tenders --------

BIDS = [
    ('TND-PAT-01', 'CONTR-05', 23.50, '2024-12-15', 1),
    ('TND-PAT-01', 'CONTR-06', 23.90, '2024-12-15', 0),
    ('TND-PAT-01', 'CONTR-07', 23.95, '2024-12-15', 0),

    ('TND-PAT-02', 'CONTR-06', 15.80, '2025-01-25', 1),
    ('TND-PAT-02', 'CONTR-05', 15.95, '2025-01-25', 0),
    ('TND-PAT-02', 'CONTR-07', 15.98, '2025-01-25', 0),

    ('TND-PAT-03', 'CONTR-07', 44.00, '2025-03-01', 1),
    ('TND-PAT-03', 'CONTR-05', 44.80, '2025-03-01', 0),
    ('TND-PAT-03', 'CONTR-06', 44.90, '2025-03-01', 0),

    ('TND-JPR-01', 'CONTR-08', 54.00, '2025-02-18', 1),
]


def build_works(cid_var, cid_del, cid_blr, cid_pat, cid_jpr, cid_wyd, get_mp_id):
    """Returns the demo works, bound to whichever constituency ids the portal
    CSV produced for Varanasi, New Delhi, Bengaluru, Patna, Jaipur and Wayanad.
    """
    return [
        # Varanasi
        ('WRK-VAR-01', cid_var, get_mp_id(cid_var), 'Solar High-Mast Light at Dashashwamedh Ghat', 'High-Mast Solar Light', 2.10, 2.10, 'Completed', '2025-01-10', '2025-05-12', 25.3076, 83.0104, 'Dashashwamedh Ghat, Varanasi', 'Varanasi Nagar Nigam', 'CONTR-01', 100, 'Normal'),
        ('WRK-VAR-02', cid_var, get_mp_id(cid_var), 'Smart Classroom at Govt Inter College', 'School Classroom / Lab', 8.20, 8.20, 'Completed', '2025-02-15', '2025-06-20', 25.3176, 82.9860, 'GIC Compound, Maldahiya', 'DRDA Varanasi', 'CONTR-02', 100, 'Normal'),

        # FRAUD 1: duplicate borewells ~45 m apart
        ('WRK-VAR-03', cid_var, get_mp_id(cid_var), 'Deep Borewell with Submersible at Sankat Mochan Ward', 'Borewell / Handpump', 1.15, 1.15, 'Completed', '2025-03-01', '2025-04-10', 25.2818, 82.9995, 'Near Sankat Mochan Temple, Ward 12', 'Varanasi Jal Sansthan', 'CONTR-01', 100, 'Critical'),
        ('WRK-VAR-04', cid_var, get_mp_id(cid_var), 'Community Drinking Water Pump Facility', 'Borewell / Handpump', 1.18, 1.18, 'Completed', '2025-04-20', '2025-06-01', 25.2821, 82.9998, 'Opposite Post Office, Ward 12', 'Varanasi Jal Sansthan', 'CONTR-02', 100, 'Critical'),

        # New Delhi
        ('WRK-DEL-01', cid_del, get_mp_id(cid_del), 'Public Health Wellness Kiosk Lodhi Colony', 'Public Health Dispensary', 42.00, 35.00, 'In Progress', '2025-04-10', '2025-08-01', 28.5833, 77.2250, 'Lodhi Colony Sector 3', 'NDMC', 'CONTR-03', 75, 'Normal'),
        ('WRK-DEL-02', cid_del, get_mp_id(cid_del), 'Solar Street Lighting in Sarojini Nagar Market', 'High-Mast Solar Light', 2.30, 2.30, 'Completed', '2025-02-01', '2025-04-15', 28.5770, 77.1950, 'Sarojini Nagar, Block B', 'NDMC', 'CONTR-03', 100, 'Normal'),

        # FRAUD 3: Bengaluru stagnant project
        ('WRK-BLR-01', cid_blr, get_mp_id(cid_blr), 'Multipurpose Community Centre at Jayanagar 4th Block', 'Community Hall / Bhavan', 24.50, 0.00, 'Delayed', '2024-10-15', '2024-11-01', 12.9298, 77.5838, 'Jayanagar 4th Block, Bengaluru', 'BBMP Zone South', 'CONTR-04', 5, 'High'),
        ('WRK-BLR-02', cid_blr, get_mp_id(cid_blr), 'Model Science Laboratory at Govt PU College Banashankari', 'School Classroom / Lab', 8.50, 8.50, 'Completed', '2025-01-10', '2025-05-18', 12.9150, 77.5736, 'Banashankari 2nd Stage', 'DRDA Bengaluru', 'CONTR-04', 100, 'Normal'),

        # FRAUD 4: Patna cartel bidding ring
        ('WRK-PAT-01', cid_pat, get_mp_id(cid_pat), 'Construction of RCC Community Hall Kankarbagh', 'Community Hall / Bhavan', 23.50, 23.50, 'Completed', '2025-01-05', '2025-06-10', 25.5941, 85.1376, 'Kankarbagh Colony, Patna', 'Patna Nagar Nigam', 'CONTR-05', 100, 'High'),
        ('WRK-PAT-02', cid_pat, get_mp_id(cid_pat), 'Concrete Road from NH-30 to Didarganj Village', 'Concrete Village Road', 15.80, 15.80, 'Completed', '2025-02-12', '2025-07-01', 25.5680, 85.2450, 'Didarganj Industrial Area', 'RWD Bihar', 'CONTR-06', 100, 'High'),
        ('WRK-PAT-03', cid_pat, get_mp_id(cid_pat), 'Health Sub-Centre Renovation at Gulzarbagh', 'Public Health Dispensary', 44.00, 44.00, 'Completed', '2025-03-20', '2025-08-15', 25.6020, 85.1950, 'Gulzarbagh, Patna City', 'BMSICL Patna', 'CONTR-07', 100, 'High'),

        # FRAUD 2: Jaipur Rural price inflation (Rs 54L road)
        ('WRK-JPR-01', cid_jpr, get_mp_id(cid_jpr), 'CC Village Road from Shahpura to Bhabhru (1.2 KM)', 'Concrete Village Road', 54.00, 54.00, 'Completed', '2025-03-10', '2025-07-25', 27.3850, 75.9600, 'Shahpura Tehsil, Jaipur Rural', 'PWD Rajasthan Zone 4', 'CONTR-08', 100, 'Critical'),
        ('WRK-JPR-02', cid_jpr, get_mp_id(cid_jpr), 'Solar High-Mast Lighting at Amer Rural Junction', 'High-Mast Solar Light', 2.40, 2.40, 'Completed', '2025-01-20', '2025-04-10', 26.9855, 75.8513, 'Amer Rural Chowk', 'DRDA Jaipur', 'CONTR-08', 100, 'Normal'),

        # Wayanad
        ('WRK-WYD-01', cid_wyd, get_mp_id(cid_wyd), 'Tribal Healthcare Dispensary at Meppadi', 'Public Health Dispensary', 45.00, 30.00, 'In Progress', '2025-03-15', '2025-08-10', 11.5510, 76.1280, 'Meppadi Panchayat, Wayanad', 'National Health Mission Kerala', 'CONTR-09', 70, 'Normal'),
    ]
