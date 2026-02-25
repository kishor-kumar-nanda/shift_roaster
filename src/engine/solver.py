"""
Constraint Programming Solver for Shift Roster Generation.
Uses Google OR-Tools CP-SAT to mathematically optimize shift assignments
while satisfying all hard constraints and optimizing soft objectives.
"""
from ortools.sat.python import cp_model
from typing import Dict, List, Optional
from datetime import date

from src.config.constants import (
    SHIFT_A, SHIFT_B, SHIFT_C, SHIFT_OG, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF,
    SHIFT_ID_TO_LABEL, LABEL_TO_SHIFT_ID, NUM_STATUSES, WORKING_SHIFTS,
    WEEKDAY_COVERAGE, WEEKEND_COVERAGE, IRM_COVERAGE,
    SENIOR_ROLES, JUNIOR_ROLES,
    MAX_CONSECUTIVE_SAME_SHIFT, TARGET_OFFS_PER_WEEK, MAX_NIGHT_SHIFTS_PER_MONTH,
)
from src.config.employees import Employee, SOLVER_EMPLOYEES


class ShiftRosterSolver:
    """
    CP-SAT based shift roster solver.
    
    Decision Variables:
        work[e, d, s] ∈ {0, 1}  — employee e is assigned status s on day d
    
    Hard Constraints:
        1. Exactly one status per employee per day
        2. Allowed shifts only
        3. Pre-assigned leaves
        4. Pre-assigned compoffs  
        5. Force assignments
        6. Minimum coverage per shift per day (weekday/weekend/IRM-adjusted)
        7. Night→Morning rest block (C shift day d → NOT A shift day d+1)
        8. Mentorship: junior on shift → at least 1 senior on same shift
        9. IRM weekend: enhanced coverage with senior presence
       10. At least 1 OFF per 7-day rolling window
    
    Soft Objectives (Optimization):
        - Fair distribution of OFFs
        - Night shift balance across employees
        - Minimize excessive same-shift streaks
    """

    def __init__(self,
                 employees: List[Employee],
                 calendar_context: Dict,
                 planned_leaves: Dict[str, List[date]] = None,
                 compoffs: Dict[str, List[date]] = None,
                 force_assignments: List[Dict] = None):
        
        self.employees = employees
        self.cal = calendar_context
        self.num_employees = len(employees)
        self.num_days = calendar_context["num_days"]
        self.dates = calendar_context["dates"]
        self.day_info = calendar_context["day_info"]

        self.planned_leaves = planned_leaves or {}
        self.compoffs = compoffs or {}
        self.force_assignments = force_assignments or []

        self.model = cp_model.CpModel()
        self.work = {}  # (employee_idx, day_idx, status_idx) -> BoolVar

        # Employee name -> index lookup
        self.name_to_idx = {emp.name: i for i, emp in enumerate(employees)}

    def build(self):
        """Build the full CP model with all constraints."""
        self._create_variables()
        self._constraint_one_status_per_day()
        self._constraint_allowed_shifts()
        self._constraint_compoff_only_pre_assigned()
        self._constraint_pre_assigned_leaves()
        self._constraint_pre_assigned_compoffs()
        self._constraint_force_assignments()
        self._constraint_minimum_coverage()
        self._constraint_night_morning_block()
        self._constraint_mentorship()
        self._constraint_irm_weekend()
        self._constraint_minimum_offs()
        self._constraint_night_shift_cap()
        self._objective_fairness()

    def solve(self, time_limit: float = 30.0) -> Optional[Dict]:
        """Run the solver. Returns roster dict or None if infeasible."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_workers = 8  # Parallel search workers

        status = solver.Solve(self.model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"    ✅ Solver status: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}")
            print(f"    📊 Objective value: {solver.ObjectiveValue()}")
            return self._extract_result(solver)
        else:
            status_name = {
                cp_model.INFEASIBLE: "INFEASIBLE",
                cp_model.MODEL_INVALID: "MODEL_INVALID",
                cp_model.UNKNOWN: "UNKNOWN (timeout?)",
            }.get(status, f"STATUS_{status}")
            print(f"    💀 Solver status: {status_name}")
            return None

    # ════════════════════════════════════════════════════════════════
    #  VARIABLE CREATION
    # ════════════════════════════════════════════════════════════════

    def _create_variables(self):
        """Create boolean decision variables for each (employee, day, status)."""
        for e in range(self.num_employees):
            for d in range(self.num_days):
                for s in range(NUM_STATUSES):
                    self.work[(e, d, s)] = self.model.new_bool_var(
                        f"w_{self.employees[e].name[:3]}_{d}_{SHIFT_ID_TO_LABEL.get(s, s)}"
                    )

    # ════════════════════════════════════════════════════════════════
    #  HARD CONSTRAINTS
    # ════════════════════════════════════════════════════════════════

    def _constraint_one_status_per_day(self):
        """C1: Each employee has exactly one status per day."""
        for e in range(self.num_employees):
            for d in range(self.num_days):
                self.model.add_exactly_one(
                    self.work[(e, d, s)] for s in range(NUM_STATUSES)
                )

    def _constraint_allowed_shifts(self):
        """C2: Employee can only be assigned to their permitted shifts/statuses."""
        for e, emp in enumerate(self.employees):
            allowed = set(emp.allowed_shifts)
            for d in range(self.num_days):
                for s in range(NUM_STATUSES):
                    if s not in allowed:
                        self.model.add(self.work[(e, d, s)] == 0)

    def _constraint_pre_assigned_leaves(self):
        """C3: Force LEAVE status on specific dates from YAML config."""
        for name, leave_dates in self.planned_leaves.items():
            if name not in self.name_to_idx:
                print(f"    ⚠️  Leave config: '{name}' not found in employees, skipping")
                continue
            e = self.name_to_idx[name]
            for ld in leave_dates:
                if ld in self.dates:
                    d = self.dates.index(ld)
                    self.model.add(self.work[(e, d, SHIFT_LEAVE)] == 1)

    def _constraint_pre_assigned_compoffs(self):
        """C4: Force COMPOFF status on specific dates from YAML config."""
        for name, compoff_dates in self.compoffs.items():
            if name not in self.name_to_idx:
                print(f"    ⚠️  CompOff config: '{name}' not found in employees, skipping")
                continue
            e = self.name_to_idx[name]
            for cd in compoff_dates:
                if cd in self.dates:
                    d = self.dates.index(cd)
                    self.model.add(self.work[(e, d, SHIFT_COMPOFF)] == 1)

    def _constraint_force_assignments(self):
        """C5: Lock specific employee+date+shift from YAML config."""
        for fa in self.force_assignments:
            name = fa["employee"]
            if name not in self.name_to_idx:
                print(f"    ⚠️  Force assignment: '{name}' not found, skipping")
                continue
            e = self.name_to_idx[name]
            fa_date = fa["date"]
            shift_label = fa["shift"]
            shift_id = LABEL_TO_SHIFT_ID.get(shift_label)
            if shift_id is None:
                print(f"    ⚠️  Force assignment: shift '{shift_label}' unknown, skipping")
                continue
            if fa_date in self.dates:
                d = self.dates.index(fa_date)
                self.model.add(self.work[(e, d, shift_id)] == 1)

    def _constraint_minimum_coverage(self):
        """C6 + C7: Minimum staff per shift, adjusted for weekdays/weekends/IRM."""
        for d in range(self.num_days):
            info = self.day_info[d]

            # Choose coverage profile based on day type
            if info["is_irm"]:
                coverage = IRM_COVERAGE
            elif info["is_weekend"]:
                coverage = WEEKEND_COVERAGE
            else:
                coverage = WEEKDAY_COVERAGE

            for shift_id, min_count in coverage.items():
                if min_count > 0:
                    self.model.add(
                        sum(self.work[(e, d, shift_id)]
                            for e in range(self.num_employees)) >= min_count
                    )

    def _constraint_night_morning_block(self):
        """C8: C shift cannot be immediately followed by A shift (< 6h rest)."""
        for e in range(self.num_employees):
            for d in range(self.num_days - 1):
                # If work[e, d, C] == 1 => work[e, d+1, A] must be 0
                self.model.add_implication(
                    self.work[(e, d, SHIFT_C)],
                    self.work[(e, d + 1, SHIFT_A)].negated()
                )

    def _constraint_mentorship(self):
        """C9: If any junior is on a working shift, at least 1 senior must be present."""
        senior_indices = [i for i, emp in enumerate(self.employees) if emp.is_senior]
        junior_indices = [i for i, emp in enumerate(self.employees) if emp.is_junior]

        if not junior_indices or not senior_indices:
            return

        for d in range(self.num_days):
            for s in WORKING_SHIFTS:
                # Sum of juniors on this shift/day
                junior_count = sum(self.work[(j, d, s)] for j in junior_indices)
                senior_count = sum(self.work[(sr, d, s)] for sr in senior_indices)

                # Reified: if any junior present, force senior presence
                any_junior = self.model.new_bool_var(f"any_jr_d{d}_s{s}")
                self.model.add(junior_count > 0).only_enforce_if(any_junior)
                self.model.add(junior_count == 0).only_enforce_if(any_junior.negated())
                self.model.add(senior_count >= 1).only_enforce_if(any_junior)

    def _constraint_irm_weekend(self):
        """C10: IRM weekend requires enhanced coverage with senior+mid-senior+mid-junior."""
        irm_sat, irm_sun = self.cal["irm_weekend"]
        irm_dates = [irm_sat, irm_sun]

        senior_indices = [i for i, emp in enumerate(self.employees)
                          if emp.role in ("Senior", "Lead") and emp.irm_eligible]
        mid_senior_indices = [i for i, emp in enumerate(self.employees)
                              if emp.role == "Mid Senior" and emp.irm_eligible]
        mid_junior_indices = [i for i, emp in enumerate(self.employees)
                              if emp.role == "Mid Junior" and emp.irm_eligible]

        for irm_date in irm_dates:
            if irm_date not in self.dates:
                continue
            d = self.dates.index(irm_date)

            # At least 1 senior working across any shift
            if senior_indices:
                self.model.add(
                    sum(self.work[(e, d, s)]
                        for e in senior_indices for s in WORKING_SHIFTS) >= 1
                )

            # At least 1 mid-senior working across any shift
            if mid_senior_indices:
                self.model.add(
                    sum(self.work[(e, d, s)]
                        for e in mid_senior_indices for s in WORKING_SHIFTS) >= 1
                )

            # At least 1 mid-junior working across any shift
            if mid_junior_indices:
                self.model.add(
                    sum(self.work[(e, d, s)]
                        for e in mid_junior_indices for s in WORKING_SHIFTS) >= 1
                )

    def _constraint_minimum_offs(self):
        """C10b: At least 1 OFF/LEAVE/COMPOFF per 9-day rolling window."""
        for e in range(self.num_employees):
            for start in range(self.num_days - 8):
                end = start + 9
                off_days = []
                for d in range(start, end):
                    for s in [SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF]:
                        off_days.append(self.work[(e, d, s)])
                self.model.add(sum(off_days) >= TARGET_OFFS_PER_WEEK)

    def _constraint_night_shift_cap(self):
        """C11: Hard cap on C (night) shifts per person per month."""
        for e in range(self.num_employees):
            if SHIFT_C in self.employees[e].allowed_shifts:
                total_c = sum(self.work[(e, d, SHIFT_C)] for d in range(self.num_days))
                self.model.add(total_c <= MAX_NIGHT_SHIFTS_PER_MONTH)

    def _constraint_compoff_only_pre_assigned(self):
        """C12: CompOff can only be assigned on dates explicitly set in YAML config."""
        # Build set of (employee_idx, day_idx) that are pre-assigned compoffs
        compoff_slots = set()
        for name, compoff_dates in self.compoffs.items():
            if name in self.name_to_idx:
                e = self.name_to_idx[name]
                for cd in compoff_dates:
                    if cd in self.dates:
                        d = self.dates.index(cd)
                        compoff_slots.add((e, d))

        # Block CompOff on all non-pre-assigned slots
        for e in range(self.num_employees):
            for d in range(self.num_days):
                if (e, d) not in compoff_slots:
                    self.model.add(self.work[(e, d, SHIFT_COMPOFF)] == 0)

    # ════════════════════════════════════════════════════════════════
    #  SOFT OBJECTIVES (OPTIMIZATION)
    # ════════════════════════════════════════════════════════════════

    def _objective_fairness(self):
        """
        Soft optimization objectives:
        1. Balance OFF days across employees
        2. Balance night shifts (C) across eligible employees
        3. Penalize long same-shift streaks
        """
        penalties = []

        # ── Objective 1: Fair OFF distribution ──────────────────────
        # Target: each person gets roughly (num_days // 7) offs
        target_offs = max(self.num_days // 7, 3)
        for e in range(self.num_employees):
            total_offs = sum(
                self.work[(e, d, s)]
                for d in range(self.num_days)
                for s in [SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF]
            )
            # Deviation from target (absolute via auxiliary variables)
            dev = self.model.new_int_var(0, self.num_days, f"off_dev_{e}")
            self.model.add(dev >= total_offs - target_offs)
            self.model.add(dev >= target_offs - total_offs)
            penalties.append(dev * 10)  # Weight: 10

        # ── Objective 2: Balance night shifts ──────────────────────
        c_eligible = [i for i, emp in enumerate(self.employees)
                      if SHIFT_C in emp.allowed_shifts]
        if len(c_eligible) > 1:
            target_c = max(self.num_days // len(c_eligible), 2)
            for e in c_eligible:
                total_c = sum(self.work[(e, d, SHIFT_C)] for d in range(self.num_days))
                dev_c = self.model.new_int_var(0, self.num_days, f"c_dev_{e}")
                self.model.add(dev_c >= total_c - target_c)
                self.model.add(dev_c >= target_c - total_c)
                penalties.append(dev_c * 5)  # Weight: 5

        # ── Objective 3: Penalize long same-shift streaks ──────────
        for e in range(self.num_employees):
            for s in WORKING_SHIFTS:
                for d in range(self.num_days - MAX_CONSECUTIVE_SAME_SHIFT):
                    streak = [self.work[(e, d + k, s)]
                              for k in range(MAX_CONSECUTIVE_SAME_SHIFT + 1)]
                    # If all MAX+1 consecutive days are the same shift, penalize
                    all_same = self.model.new_bool_var(
                        f"streak_{e}_{s}_{d}"
                    )
                    self.model.add(
                        sum(streak) == MAX_CONSECUTIVE_SAME_SHIFT + 1
                    ).only_enforce_if(all_same)
                    self.model.add(
                        sum(streak) < MAX_CONSECUTIVE_SAME_SHIFT + 1
                    ).only_enforce_if(all_same.negated())
                    # Penalize the streak violation
                    penalty_var = self.model.new_int_var(0, 100, f"sp_{e}_{s}_{d}")
                    self.model.add(penalty_var == 100).only_enforce_if(all_same)
                    self.model.add(penalty_var == 0).only_enforce_if(all_same.negated())
                    penalties.append(penalty_var)

        # Minimize total penalty
        if penalties:
            self.model.minimize(sum(penalties))

    # ════════════════════════════════════════════════════════════════
    #  RESULT EXTRACTION
    # ════════════════════════════════════════════════════════════════

    def _extract_result(self, solver: cp_model.CpSolver) -> Dict:
        """
        Extract solved roster as structured dict.
        
        Returns:
            {
                "roster": [
                    {"name": "Deepak", "shifts": ["A", "B", "OFF", "A", ...]},
                    ...
                ],
                "coverage": {day_idx: {"A": count, "B": count, ...}, ...},
                "stats": {name: {"A": n, "B": n, ...}, ...}
            }
        """
        roster = []
        coverage = {}
        stats = {}

        for e in range(self.num_employees):
            emp = self.employees[e]
            shifts = []
            emp_stats = {}

            for d in range(self.num_days):
                for s in range(NUM_STATUSES):
                    if solver.value(self.work[(e, d, s)]):
                        label = SHIFT_ID_TO_LABEL[s]
                        shifts.append(label)
                        emp_stats[label] = emp_stats.get(label, 0) + 1

                        # Coverage tracking
                        if d not in coverage:
                            coverage[d] = {}
                        coverage[d][label] = coverage[d].get(label, 0) + 1
                        break

            roster.append({"name": emp.name, "shifts": shifts})
            stats[emp.name] = emp_stats

        return {
            "roster": roster,
            "coverage": coverage,
            "stats": stats,
        }
