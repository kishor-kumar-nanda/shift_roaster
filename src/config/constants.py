"""
Shift definitions, color mappings, and timing constants.
All colors matched to user's existing Excel roster format.
"""

# ─── Shift ID Mapping ──────────────────────────────────────────────
SHIFT_A = 0   # Morning
SHIFT_B = 1   # Afternoon
SHIFT_C = 2   # Night
SHIFT_OG = 3  # Offshore General
SHIFT_OFF = 4
SHIFT_LEAVE = 5
SHIFT_COMPOFF = 6
SHIFT_TCS_HOLIDAY = 7
SHIFT_CIGNA_HOLIDAY = 8

SHIFT_ID_TO_LABEL = {
    SHIFT_A: "A",
    SHIFT_B: "B",
    SHIFT_C: "C",
    SHIFT_OG: "OG",
    SHIFT_OFF: "OFF",
    SHIFT_LEAVE: "Leave",
    SHIFT_COMPOFF: "CompOff",
    SHIFT_TCS_HOLIDAY: "TH",
    SHIFT_CIGNA_HOLIDAY: "CH",
}

LABEL_TO_SHIFT_ID = {v: k for k, v in SHIFT_ID_TO_LABEL.items()}

# Only these are "working" shifts that need coverage
WORKING_SHIFTS = [SHIFT_A, SHIFT_B, SHIFT_C, SHIFT_OG]

# Total number of statuses (for solver variable domain)
NUM_STATUSES = len(SHIFT_ID_TO_LABEL)

# ─── Shift Timings ─────────────────────────────────────────────────
SHIFT_TIMINGS = {
    "A": {"IST": "6:00 AM - 3:00 PM",  "EST": "8:30 PM - 5:30 AM (prev day)"},
    "B": {"IST": "2:00 PM - 10:00 PM", "EST": "4:30 AM - 1:30 PM"},
    "C": {"IST": "10:00 PM - 7:00 AM", "EST": "12:30 PM - 9:30 PM"},
    "OG":{"IST": "9:30 AM - 6:30 PM",  "EST": "12:00 AM - 9:00 AM"},
}

# ─── Excel Cell Colors (ARGB hex for openpyxl) ────────────────────
SHIFT_COLORS = {
    "A":       "FF92D050",   # Green
    "B":       "FF4472C4",   # Blue
    "C":       "FFFFFF00",   # Yellow
    "OG":      "FFF4B084",   # Orange/Peach
    "OFF":     "FFFFFFFF",   # White
    "Leave":   "FFD5A6BD",   # Pink/Purple
    "CompOff": "FFB4A7D6",   # Lavender
    "TH":      "FFFF0000",   # Red (TCS Holiday)
    "CH":      "FF0070C0",   # Blue (Cigna Holiday)
}

# Font colors for contrast
SHIFT_FONT_COLORS = {
    "A":       "FF000000",   # Black on Green
    "B":       "FFFFFFFF",   # White on Blue
    "C":       "FF000000",   # Black on Yellow
    "OG":      "FF000000",   # Black on Orange
    "OFF":     "FF808080",   # Gray on White
    "Leave":   "FF000000",   # Black on Pink
    "CompOff": "FF000000",   # Black on Lavender
    "TH":      "FFFFFFFF",   # White on Red
    "CH":      "FFFFFFFF",   # White on Blue
}

# ─── Coverage Requirements ─────────────────────────────────────────
# Weekday minimums
WEEKDAY_COVERAGE = {
    SHIFT_A:  3,
    SHIFT_B:  1,
    SHIFT_C:  1,
    SHIFT_OG: 1,
}

# Weekend minimums (reduced)
WEEKEND_COVERAGE = {
    SHIFT_A:  2,
    SHIFT_B:  0,
    SHIFT_C:  1,
    SHIFT_OG: 0,
}

# IRM Weekend minimums (3rd weekend — heavier coverage needed)
IRM_COVERAGE = {
    SHIFT_A:  2,
    SHIFT_B:  1,
    SHIFT_C:  1,
    SHIFT_OG: 1,
}

# ─── Role Hierarchy ───────────────────────────────────────────────
SENIORITY_RANKS = {
    "Lead": 1,
    "Senior": 2,
    "Mid Senior": 3,
    "Mid Junior": 4,
    "Junior": 5,
}

# Roles that count as "senior" for mentorship constraint
SENIOR_ROLES = {"Lead", "Senior", "Mid Senior"}
JUNIOR_ROLES = {"Mid Junior", "Junior"}

# ─── Solver Targets ───────────────────────────────────────────────
MAX_CONSECUTIVE_SAME_SHIFT = 6   # Soft limit before rotation
TARGET_OFFS_PER_WEEK = 1         # Minimum target offs per 7-day window
MAX_NIGHT_SHIFTS_PER_MONTH = 10  # Hard cap on C shifts per person
