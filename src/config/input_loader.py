"""
YAML-based monthly input configuration loader.
Reads leaves, compoffs, holidays, force-assignments from user-editable YAML file.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from src.engine.calendar_utils import parse_date_string


def load_monthly_config(config_path: str) -> Dict:
    """
    Load and parse the monthly YAML configuration file.
    
    Expected YAML structure:
    ```yaml
    month: 3
    year: 2026
    holidays:
      tcs: ["2026-03-10"]
      cigna: ["2026-03-17"]
    planned_leaves:
      Pradheep: ["2026-03-05", "2026-03-06"]
    compoffs:
      Deepak: ["2026-03-02"]
    force_assignments:
      - employee: "Deepak"
        date: "2026-03-15"
        shift: "A"
    irm_weekend_override: null
    ```
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    config = {
        "month": raw.get("month"),
        "year": raw.get("year"),
        "tcs_holidays": raw.get("holidays", {}).get("tcs", []),
        "cigna_holidays": raw.get("holidays", {}).get("cigna", []),
        "planned_leaves": {},
        "compoffs": {},
        "force_assignments": [],
        "irm_weekend_override": None,
    }

    # Parse planned leaves: name -> list of date objects
    raw_leaves = raw.get("planned_leaves", {})
    if raw_leaves:
        for name, date_strs in raw_leaves.items():
            config["planned_leaves"][name] = [parse_date_string(ds) for ds in date_strs]

    # Parse compoffs: name -> list of date objects
    raw_compoffs = raw.get("compoffs", {})
    if raw_compoffs:
        for name, date_strs in raw_compoffs.items():
            config["compoffs"][name] = [parse_date_string(ds) for ds in date_strs]

    # Parse force assignments: list of {employee, date, shift_label}
    raw_force = raw.get("force_assignments", [])
    if raw_force:
        for fa in raw_force:
            config["force_assignments"].append({
                "employee": fa["employee"],
                "date": parse_date_string(fa["date"]),
                "shift": fa["shift"],
            })

    # IRM override
    raw_irm = raw.get("irm_weekend_override")
    if raw_irm and isinstance(raw_irm, list) and len(raw_irm) == 2:
        config["irm_weekend_override"] = (raw_irm[0], raw_irm[1])

    return config


def create_sample_config(output_path: str, month: int, year: int):
    """Generate a sample YAML config file for a given month."""
    sample = {
        "month": month,
        "year": year,
        "holidays": {
            "tcs": [],
            "cigna": [],
        },
        "planned_leaves": {
            "# Employee_Name": ["YYYY-MM-DD"],
        },
        "compoffs": {
            "# Employee_Name": ["YYYY-MM-DD"],
        },
        "force_assignments": [
            {
                "employee": "# Employee_Name",
                "date": "YYYY-MM-DD",
                "shift": "A",
            }
        ],
        "irm_weekend_override": None,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        yaml.dump(sample, f, default_flow_style=False, sort_keys=False)

    print(f"📝 Sample config created at: {output_path}")
