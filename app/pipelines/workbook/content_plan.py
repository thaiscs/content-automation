"""
Monthly content-plan lookup.

Reads content_plan.toml and returns the theme + objectives for a given month,
plus the human-readable Italian edition label (e.g. "Luglio 2026") shown on the
cover. Giusi maintains the plan a few editions ahead; the monthly cron reads the
current month's entry and never invents a theme on its own.
"""

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_PLAN_PATH = Path(__file__).resolve().parents[3] / "content_plan.toml"

_MESI_IT = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
    5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre",
}


@dataclass
class Edition:
    key: str          # "2026-07"
    label: str        # "Luglio 2026"
    tema: str
    obiettivi: str


def edition_label(d: date) -> str:
    return f"{_MESI_IT[d.month]} {d.year}"


def load_edition(d: date, plan_path: Path | None = None) -> Edition | None:
    """
    Return the Edition planned for month `d`, or None if there's no entry.
    `d` is any date in the target month (typically today).
    """
    path = plan_path or _PLAN_PATH
    if not path.exists():
        return None

    with path.open("rb") as f:
        plan = tomllib.load(f)

    key = f"{d.year:04d}-{d.month:02d}"
    entry = plan.get(key)
    if not entry or not entry.get("tema"):
        return None

    return Edition(
        key=key,
        label=edition_label(d),
        tema=entry["tema"],
        obiettivi=entry.get("obiettivi", ""),
    )
