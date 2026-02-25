"""
Calendar utilities for date generation, IRM weekend detection, and weekend identification.
"""
import calendar
from datetime import date, timedelta
from typing import List, Tuple, Dict, Optional


def get_month_dates(year: int, month: int) -> List[date]:
    """Generate all dates for a given month/year."""
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, d) for d in range(1, num_days + 1)]


def get_day_name(d: date) -> str:
    """Short day name: Mon, Tue, Wed, etc."""
    return d.strftime("%a")


def format_date_header(d: date) -> str:
    """Format date as '1-Feb', '2-Feb', etc. matching existing roster format."""
    return f"{d.day}-{d.strftime('%b')}"


def is_weekend(d: date) -> bool:
    """Saturday = 5, Sunday = 6."""
    return d.weekday() >= 5


def get_irm_weekend(year: int, month: int) -> Tuple[date, date]:
    """
    Get the 3rd weekend (Saturday + Sunday) of the month.
    This is the IRM (Monthly IRM) weekend.
    """
    saturdays = []
    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        d = date(year, month, day)
        if d.weekday() == 5:  # Saturday
            saturdays.append(d)

    if len(saturdays) >= 3:
        irm_sat = saturdays[2]
        irm_sun = irm_sat + timedelta(days=1)
        return (irm_sat, irm_sun)
    else:
        # Fallback: last weekend if month is short
        irm_sat = saturdays[-1]
        irm_sun = irm_sat + timedelta(days=1)
        return (irm_sat, irm_sun)


def is_irm_date(d: date, irm_weekend: Tuple[date, date]) -> bool:
    """Check if date falls on IRM weekend."""
    return d == irm_weekend[0] or d == irm_weekend[1]


def get_week_index(d: date, month_dates: List[date]) -> int:
    """Get which week of the month a date belongs to (0-indexed)."""
    first_day = month_dates[0]
    return (d - first_day).days // 7


def parse_date_string(date_str: str) -> date:
    """Parse 'YYYY-MM-DD' string to date object."""
    parts = date_str.split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


def build_calendar_context(year: int, month: int,
                           tcs_holidays: List[str] = None,
                           cigna_holidays: List[str] = None,
                           irm_override: Optional[Tuple[str, str]] = None
                           ) -> Dict:
    """
    Build the full calendar context for a month.
    Returns a dict with all date metadata needed by solver and writer.
    """
    month_dates = get_month_dates(year, month)

    # IRM weekend
    if irm_override:
        irm_weekend = (parse_date_string(irm_override[0]),
                       parse_date_string(irm_override[1]))
    else:
        irm_weekend = get_irm_weekend(year, month)

    # Parse holidays
    tcs_set = set()
    if tcs_holidays:
        tcs_set = {parse_date_string(h) for h in tcs_holidays}

    cigna_set = set()
    if cigna_holidays:
        cigna_set = {parse_date_string(h) for h in cigna_holidays}

    # Build per-day metadata
    day_info = []
    for d in month_dates:
        info = {
            "date": d,
            "date_header": format_date_header(d),
            "day_name": get_day_name(d),
            "is_weekend": is_weekend(d),
            "is_irm": is_irm_date(d, irm_weekend),
            "is_tcs_holiday": d in tcs_set,
            "is_cigna_holiday": d in cigna_set,
            "week_index": get_week_index(d, month_dates),
        }
        day_info.append(info)

    return {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "num_days": len(month_dates),
        "dates": month_dates,
        "irm_weekend": irm_weekend,
        "tcs_holidays": tcs_set,
        "cigna_holidays": cigna_set,
        "day_info": day_info,
    }
