"""
Shift Roster Engine V2 — CLI Entry Point.

Usage:
    python src/main.py --config input/march_2026.yaml
    python src/main.py --month 3 --year 2026
    python src/main.py  (defaults to current month)
"""
import sys
import os
import argparse
from datetime import date

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.employees import SOLVER_EMPLOYEES
from src.config.input_loader import load_monthly_config, create_sample_config
from src.engine.calendar_utils import build_calendar_context
from src.engine.solver import ShiftRosterSolver
from src.output.excel_writer import write_roster_excel


def main():
    parser = argparse.ArgumentParser(description="🚀 Shift Roster Engine V2")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to YAML config file (e.g., input/march_2026.yaml)")
    parser.add_argument("--month", type=int, default=None,
                        help="Month number (1-12)")
    parser.add_argument("--year", type=int, default=None,
                        help="Year (e.g., 2026)")
    parser.add_argument("--time-limit", type=float, default=30.0,
                        help="Solver time limit in seconds (default: 30)")
    parser.add_argument("--generate-sample", action="store_true",
                        help="Generate a sample YAML config and exit")
    args = parser.parse_args()

    # ─── Sample Config Generation ─────────────────────────────────
    if args.generate_sample:
        m = args.month or date.today().month
        y = args.year or date.today().year
        output = f"input/sample_{date(y, m, 1).strftime('%B').lower()}_{y}.yaml"
        create_sample_config(output, m, y)
        return

    # ─── Load Config ──────────────────────────────────────────────
    if args.config:
        print(f"📂 Loading config: {args.config}")
        config = load_monthly_config(args.config)
        month = config["month"]
        year = config["year"]
    else:
        month = args.month or date.today().month
        year = args.year or date.today().year
        config = {
            "tcs_holidays": [],
            "cigna_holidays": [],
            "planned_leaves": {},
            "compoffs": {},
            "force_assignments": [],
            "irm_weekend_override": None,
        }

    print(f"\n{'='*60}")
    print(f"  🚀 SHIFT ROSTER ENGINE V2")
    print(f"  📅 Generating roster for: {date(year, month, 1).strftime('%B %Y')}")
    print(f"{'='*60}\n")

    # ─── Build Calendar Context ───────────────────────────────────
    print("📅 Building calendar context...")
    cal_context = build_calendar_context(
        year=year,
        month=month,
        tcs_holidays=config.get("tcs_holidays", []),
        cigna_holidays=config.get("cigna_holidays", []),
        irm_override=config.get("irm_weekend_override"),
    )
    irm_sat, irm_sun = cal_context["irm_weekend"]
    print(f"    ✅ {cal_context['num_days']} days in {cal_context['month_name']}")
    print(f"    🎯 IRM Weekend: {irm_sat.strftime('%d-%b')} (Sat) + {irm_sun.strftime('%d-%b')} (Sun)")
    if cal_context["tcs_holidays"]:
        print(f"    🔴 TCS Holidays: {[d.strftime('%d-%b') for d in cal_context['tcs_holidays']]}")
    if cal_context["cigna_holidays"]:
        print(f"    🔵 Cigna Holidays: {[d.strftime('%d-%b') for d in cal_context['cigna_holidays']]}")

    # ─── Initialize Solver ────────────────────────────────────────
    print("\n⚙️  Initializing Constraint Solver...")
    print(f"    👥 Employees in solver: {len(SOLVER_EMPLOYEES)}")
    if config.get("planned_leaves"):
        for name, dates in config["planned_leaves"].items():
            print(f"    📋 {name}: {len(dates)} leave day(s)")
    if config.get("compoffs"):
        for name, dates in config["compoffs"].items():
            print(f"    🔄 {name}: {len(dates)} compoff(s)")

    solver = ShiftRosterSolver(
        employees=SOLVER_EMPLOYEES,
        calendar_context=cal_context,
        planned_leaves=config.get("planned_leaves", {}),
        compoffs=config.get("compoffs", {}),
        force_assignments=config.get("force_assignments", []),
    )

    # ─── Build & Solve ────────────────────────────────────────────
    print("\n🧠 Building constraint model...")
    solver.build()
    
    print(f"🔥 Solving (time limit: {args.time_limit}s)...")
    result = solver.solve(time_limit=args.time_limit)

    if result is None:
        print("\n💀 INFEASIBLE! Constraints are too tight.")
        print("    Try: reduce leave conflicts, adjust coverage minimums, or add more employees.")
        sys.exit(1)

    # ─── Write Excel Output ───────────────────────────────────────
    month_name = cal_context["month_name"]
    output_path = f"output/Roster_{month_name}_{year}.xlsx"
    print(f"\n📊 Writing Excel output...")
    write_roster_excel(result, cal_context, output_path)

    # ─── Print Stats ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  📈 SHIFT DISTRIBUTION SUMMARY")
    print(f"{'='*60}")
    stats = result["stats"]
    print(f"\n  {'Name':<15} {'A':>4} {'B':>4} {'C':>4} {'OG':>4} {'OFF':>5} {'Leave':>6} {'CompOff':>8}")
    print(f"  {'─'*55}")
    for name, s in stats.items():
        print(f"  {name:<15} {s.get('A',0):>4} {s.get('B',0):>4} {s.get('C',0):>4} "
              f"{s.get('OG',0):>4} {s.get('OFF',0):>5} {s.get('Leave',0):>6} {s.get('CompOff',0):>8}")

    print(f"\n✅ Roster generated successfully: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
