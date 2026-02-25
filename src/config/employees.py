"""
Employee data model and roster definitions.
Fixed employees (Madhukar, Mukesh, Archith) are excluded from solver.
"""
from dataclasses import dataclass, field
from typing import List
from src.config.constants import (
    SHIFT_A, SHIFT_B, SHIFT_C, SHIFT_OG, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF,
    SENIORITY_RANKS,
)


@dataclass
class Employee:
    name: str
    role: str
    allowed_shifts: List[int]
    is_fixed: bool = False
    fixed_shift: int = -1            # Only used if is_fixed=True
    weekend_off: bool = False        # If True, Sat/Sun = OFF (used for fixed employees)
    irm_eligible: bool = True
    max_weekly_offs: int = 2
    description: str = ""

    @property
    def seniority_rank(self) -> int:
        return SENIORITY_RANKS.get(self.role, 99)

    @property
    def is_senior(self) -> bool:
        return self.role in {"Lead", "Senior", "Mid Senior"}

    @property
    def is_junior(self) -> bool:
        return self.role in {"Mid Junior", "Junior"}


# ─── All Solver-Managed Employees ────────────────────────────────
# These are the people whose shifts the solver will optimize.
# allowed_shifts includes OFF and LEAVE as possible states.

# CompOff is in allowed_shifts domain but C12 constraint blocks free assignment —
# only YAML pre-assigned dates can use it
ALL_SHIFTS = [SHIFT_A, SHIFT_B, SHIFT_C, SHIFT_OG, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF]

SOLVER_EMPLOYEES: List[Employee] = [
    Employee(
        name="Vishnu Polkar",
        role="Senior",
        allowed_shifts=[SHIFT_OG, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF],
        description="Senior, only in OG shift",
    ),
    Employee(
        name="Mallesh",
        role="Lead",
        allowed_shifts=[SHIFT_A, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF],
        description="Lead, only in A shift. Flexible for critical days",
    ),
    Employee(
        name="Pradheep",
        role="Senior",
        allowed_shifts=[SHIFT_A, SHIFT_OG, SHIFT_C, SHIFT_OFF, SHIFT_LEAVE, SHIFT_COMPOFF],
        description="Senior. A, OG, C shifts. Flexible for critical days",
    ),
    Employee(
        name="Nagendra",
        role="Mid Senior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Senior. All shifts. Handles things generally, needs some senior",
    ),
    Employee(
        name="Deepak",
        role="Mid Senior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Senior. All shifts. Major technical, required for critical tasks",
        irm_eligible=True,
    ),
    Employee(
        name="Sandeep",
        role="Mid Senior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Senior. All shifts. Major technical, required for critical tasks",
        irm_eligible=True,
    ),
    Employee(
        name="Subbarayudu",
        role="Mid Junior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Junior. All shifts. Flexible, shift covering, heavy task force",
        irm_eligible=True,
    ),
    Employee(
        name="Narendra",
        role="Mid Junior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Junior. All shifts. Flexible, shift covering, heavy task force",
        irm_eligible=True,
    ),
    Employee(
        name="Alekhya",
        role="Mid Senior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Mid Senior. All shifts. Handles things generally, needs some senior",
    ),
    Employee(
        name="Vijay",
        role="Junior",
        allowed_shifts=ALL_SHIFTS.copy(),
        description="Junior. All shifts. Strictly needs senior/mid-senior atleast",
    ),
]


# ─── Fixed Employees (NOT solver-managed, just rendered in Excel) ─
FIXED_EMPLOYEES: List[Employee] = [
    Employee(
        name="Madhukar",
        role="Senior",
        allowed_shifts=[SHIFT_OG],
        is_fixed=True,
        fixed_shift=SHIFT_OG,
        description="Onshore. Fixed OG shift, no changes.",
    ),
    Employee(
        name="Mukesh",
        role="Senior",
        allowed_shifts=[SHIFT_OG],
        is_fixed=True,
        fixed_shift=SHIFT_OG,
        description="Onshore. Fixed OG shift, no changes.",
    ),
    Employee(
        name="Archith",
        role="Mid Junior",
        allowed_shifts=[SHIFT_B],
        is_fixed=True,
        fixed_shift=SHIFT_B,
        weekend_off=True,
        description="Fixed B shift weekdays, OFF on Sat/Sun.",
    ),
]
