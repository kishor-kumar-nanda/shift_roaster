# 📊 Shift Roster Engine — User Manual

> Auto-generates monthly shift rosters with proper coloring, dates, and all constraints.
> You just edit one YAML file → run one command → get the Excel output.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Open Terminal & Go to Project Folder

```bash
cd /path/to/shift_roster_engine
source venv/bin/activate
```

### Step 2: Edit the YAML Input File

Open the file `input/march_2026.yaml` (or copy it for a new month).
This is the **ONLY file you need to edit**. Details below.

### Step 3: Run the Engine

```bash
python src/main.py --config input/march_2026.yaml
```

✅ Output Excel file will be saved in: `output/Roster_March_2026.xlsx`

---

## 📝 How to Create Input for a New Month

### Option A: Copy & Edit

```bash
# Copy the sample file
cp input/march_2026.yaml input/april_2026.yaml

# Edit it with your favorite editor
open input/april_2026.yaml
```

### Option B: Auto-Generate Blank Template

```bash
python src/main.py --generate-sample --month 4 --year 2026
# Creates: input/sample_april_2026.yaml
```

---

## 📋 YAML Input File — Field-by-Field Guide

Here's what each section means and how to fill it:

```yaml
# ─── 1. MONTH & YEAR ──────────────────────────────────────────
# Which month to generate the roster for
month: 4          # April = 4, May = 5, etc.
year: 2026

# ─── 2. HOLIDAYS ──────────────────────────────────────────────
# Format: "YYYY-MM-DD" (Year-Month-Day in quotes)
holidays:
  tcs:
    - "2026-04-14"    # Ambedkar Jayanti
    - "2026-04-21"    # Ram Navami
  cigna:
    - "2026-04-02"    # Good Friday

# ─── 3. PLANNED LEAVES ────────────────────────────────────────
# Employee Name (EXACT spelling) → list of leave dates
# These dates will be LOCKED as "Leave" in the output
planned_leaves:
  Pradheep:
    - "2026-04-05"
    - "2026-04-06"
  Subbarayudu:
    - "2026-04-20"
    - "2026-04-21"
    - "2026-04-22"

# ─── 4. COMP-OFFS ─────────────────────────────────────────────
# Same format: Employee Name → dates
# These dates will show "CompOff" in the output
compoffs:
  Deepak:
    - "2026-04-02"
  Nagendra:
    - "2026-04-15"

# ─── 5. FORCE ASSIGNMENTS ─────────────────────────────────────
# Use when you MUST have a specific person on a specific shift
# on a specific date (e.g., for IRM or critical deployments)
force_assignments:
  - employee: "Deepak"
    date: "2026-04-18"       # IRM Saturday
    shift: "A"               # Must be: A, B, C, or OG
  - employee: "Sandeep"
    date: "2026-04-19"       # IRM Sunday
    shift: "A"

# ─── 6. IRM WEEKEND OVERRIDE ──────────────────────────────────
# The engine auto-detects the 3rd weekend of the month for IRM.
# If IRM falls on a DIFFERENT weekend, override it here:
irm_weekend_override: null   # null = auto-detect (default)
# To override: ["2026-04-25", "2026-04-26"]
```

---

## ✅ Employee Names — Exact Spelling Reference

Use these exact names in the YAML file (case-sensitive):

| Name | Role | Default Shifts |
|------|------|-------|
| `Vishnu Polkar` | Senior | OG only |
| `Mallesh` | Lead | A only |
| `Pradheep` | Senior | A, C, OG |
| `Nagendra` | Mid Senior | All |
| `Deepak` | Mid Senior | All |
| `Sandeep` | Mid Senior | All |
| `Alekhya` | Mid Senior | All |
| `Subbarayudu` | Mid Junior | All |
| `Narendra` | Mid Junior | All |
| `Vijay` | Junior | All |

**Fixed (no changes needed):**
- `Madhukar` — Always OG
- `Mukesh` — Always OG
- `Archith` — Always B (weekdays), OFF on Sat/Sun

---

## 📅 Date Format

Always use: `"YYYY-MM-DD"` (with quotes)

| Date | Format |
|------|--------|
| April 5, 2026 | `"2026-04-05"` |
| April 18, 2026 | `"2026-04-18"` |
| December 25, 2026 | `"2026-12-25"` |

---

## 🔧 Running Commands

```bash
# Activate the environment (do this once per terminal session)
cd /path/to/shift_roster_engine
source venv/bin/activate

# Generate roster from config
python src/main.py --config input/april_2026.yaml

# Generate with longer solve time (if you get timeout issues)
python src/main.py --config input/april_2026.yaml --time-limit 120

# Generate blank template for any month
python src/main.py --generate-sample --month 5 --year 2026
```

---

## 📊 Output

The Excel file will be in: `output/Roster_<Month>_<Year>.xlsx`

**What's in it:**
- Row 1: Dates (1-Apr, 2-Apr, etc.)
- Row 2: Day names (Mon, Tue, etc.)
- Row 3: IRM marker (on 3rd weekend)
- Employee rows with color-coded shifts
- Summary counts (A, B, OG, C totals per day)
- Legend with shift timings in IST and EST

**Color Guide:**
| Color | Meaning |
|-------|---------|
| 🟢 Green | A Shift (6AM-3PM IST) |
| 🔵 Blue | B Shift (2PM-10PM IST) |
| 🟡 Yellow | C Shift (10PM-7AM IST) |
| 🟠 Orange | OG Shift (9:30AM-6:30PM IST) |
| ⬜ White | OFF |
| 🟣 Pink | Leave |
| 🟤 Lavender | CompOff |

---

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| "INFEASIBLE" error | Too many leaves on the same dates. Reduce conflicts or spread leaves across different days |
| Employee name not found | Check exact spelling from the table above (case-sensitive) |
| Wrong IRM weekend | Use `irm_weekend_override` in the YAML |
| Need different coverage | Edit `src/config/constants.py` → `WEEKDAY_COVERAGE`, `WEEKEND_COVERAGE` |
| Need to add a new employee | Edit `src/config/employees.py` → add to `SOLVER_EMPLOYEES` list |

---

## 📂 Monthly Workflow Checklist

- [ ] Copy `input/march_2026.yaml` → `input/<new_month>.yaml`
- [ ] Update `month` and `year` fields
- [ ] Add TCS/Cigna holidays for that month
- [ ] Collect leave requests from team and add to `planned_leaves`
- [ ] Add any compoffs
- [ ] Add force assignments for IRM weekend (if needed)
- [ ] Run: `python src/main.py --config input/<new_month>.yaml`
- [ ] Open the Excel and review
- [ ] Share with team

---

## 🛠️ First-Time Setup (One-Time Only)

If setting up on a new machine:

```bash
cd /path/to/shift_roster_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

That's it. You're ready to generate rosters!
