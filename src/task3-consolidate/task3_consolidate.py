"""
task3_consolidate.py тАФ ╨Ч╨░╨┤╨░╤З╨░ 3: ╨Ю╨▒╤К╨╡╨┤╨╕╨╜╨╡╨╜╨╕╨╡ 3 CSV-╨▓╤Л╨│╤А╤Г╨╖╨╛╨║ ╨╕╨╖ ╤А╨░╨╖╨╜╤Л╤Е ╤А╨╡╨║╨╗╨░╨╝╨╜╤Л╤Е ╤Б╨╡╤В╨╡╨╣.

╨з╨╕╤В╨░╨╡╤В 3 CSV-╤Д╨░╨╣╨╗╨░ (╨Ы╨╕╤Б╤В1, ╨Ы╨╕╤Б╤В2, ╨Ы╨╕╤Б╤В3) ╨║╨░╨╢╨┤╤Л╨╣ ╨▓ ╤Б╨▓╨╛╤С╨╝ ╤Д╨╛╤А╨╝╨░╤В╨╡,
╨┐╨░╤А╤Б╨╕╤В ╨╕ ╨┐╤А╨╕╨▓╨╛╨┤╨╕╤В ╨╕╤Е ╨║ ╨╡╨┤╨╕╨╜╨╛╨╝╤Г ╤Д╨╛╤А╨╝╨░╤В╤Г, ╨╖╨░╤В╨╡╨╝ ╨▓╤Л╨▓╨╛╨┤╨╕╤В ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В.

╨Ф╨╛╨┐╤Г╤Й╨╡╨╜╨╕╤П:
  - ╨а╨░╤Б╤Е╨╛╨┤╤Л ╨┐╨╛ ╨Ы╨╕╤Б╤В3 ╤Г╨║╨░╨╖╨░╨╜╤Л ╨▓ USD; ╨║╤Г╤А╤Б ~90 ╤А╤Г╨▒/$ (╤Г╨║╨░╨╖╨░╨╜ ╨▓ ╨║╨╛╨┤╨╡).
  - ╨Ъ╨░╨╜╨╛╨╜╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨║╨░╨╝╨┐╨░╨╜╨╕╨╣: "╨а╨Ъ 1", "╨а╨Ъ 2", "╨а╨Ъ 3".
  - ╨Х╨┤╨╕╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨░╤В╤Л: ╨Ф╨Ф.╨Ь╨Ь.╨У╨У (╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╤Г╨╡╤В ╨╕╤Б╤Е╨╛╨┤╨╜╤Л╨╝ ╨┤╨░╨╜╨╜╤Л╨╝).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from print_utils import print_header_block

# ---------------------------------------------------------------------------
# ╨Ъ╨╛╨╜╤Б╤В╨░╨╜╤В╤Л
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

FILES: Dict[str, Path] = {
    "╨Ы╨╕╤Б╤В1": BASE_DIR / "╨в╨╡╤Б╤В╨╛╨▓╨╛╨╡ ╨╝╨░╤А╨║╨╡╤В╨╛╨╗╨╛╨│╤Г 2024, ╨╖╨░╨┤╨░╤З╨░ 3 - ╨Ы╨╕╤Б╤В1.csv",
    "╨Ы╨╕╤Б╤В2": BASE_DIR / "╨в╨╡╤Б╤В╨╛╨▓╨╛╨╡ ╨╝╨░╤А╨║╨╡╤В╨╛╨╗╨╛╨│╤Г 2024, ╨╖╨░╨┤╨░╤З╨░ 3 - ╨Ы╨╕╤Б╤В2.csv",
    "╨Ы╨╕╤Б╤В3": BASE_DIR / "╨в╨╡╤Б╤В╨╛╨▓╨╛╨╡ ╨╝╨░╤А╨║╨╡╤В╨╛╨╗╨╛╨│╤Г 2024, ╨╖╨░╨┤╨░╤З╨░ 3 - ╨Ы╨╕╤Б╤В3.csv",
}

# ╨Ъ╤Г╤А╤Б: 1 USD тЙИ 90 RUB (╨┐╤А╨╕╨▒╨╗╨╕╨╖╨╕╤В╨╡╨╗╤М╨╜╨╛ Q1 2024)
USD_TO_RUB = 90.0

# ╨б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╕╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╣ ╨╝╨╡╤Б╤П╤Ж╨╡╨▓ ╨┤╨╗╤П ╤Д╨╛╤А╨╝╨░╤В╨░ ╨┤╨░╤В╤Л ╨Ы╨╕╤Б╤В3 ("╨Ь╨░╤А╤В 2024, 1")
RUSSIAN_MONTHS: Dict[str, str] = {
    "╤П╨╜╨▓╨░╤А╤М": "01", "╤П╨╜╨▓╨░╤А╤П": "01",
    "╤Д╨╡╨▓╤А╨░╨╗╤М": "02", "╤Д╨╡╨▓╤А╨░╨╗╤П": "02",
    "╨╝╨░╤А╤В": "03", "╨╝╨░╤А╤В╨░": "03",
    "╨░╨┐╤А╨╡╨╗╤М": "04", "╨░╨┐╤А╨╡╨╗╤П": "04",
    "╨╝╨░╨╣": "05", "╨╝╨░╤П": "05",
    "╨╕╤О╨╜╤М": "06", "╨╕╤О╨╜╤П": "06",
    "╨╕╤О╨╗╤М": "07", "╨╕╤О╨╗╤П": "07",
    "╨░╨▓╨│╤Г╤Б╤В": "08", "╨░╨▓╨│╤Г╤Б╤В╨░": "08",
    "╤Б╨╡╨╜╤В╤П╨▒╤А╤М": "09", "╤Б╨╡╨╜╤В╤П╨▒╤А╤П": "09",
    "╨╛╨║╤В╤П╨▒╤А╤М": "10", "╨╛╨║╤В╤П╨▒╤А╤П": "10",
    "╨╜╨╛╤П╨▒╤А╤М": "11", "╨╜╨╛╤П╨▒╤А╤П": "11",
    "╨┤╨╡╨║╨░╨▒╤А╤М": "12", "╨┤╨╡╨║╨░╨▒╤А╤П": "12",
}

# ╨б╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨╕╤Б╤Е╨╛╨┤╨╜╤Л╤Е ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╣ ╨║╨░╨╝╨┐╨░╨╜╨╕╨╣ ╤Б ╨║╨░╨╜╨╛╨╜╨╕╤З╨╡╤Б╨║╨╕╨╝╨╕
CANONICAL_CAMPAIGNS: Dict[str, str] = {
    "╨а╨Ъ1": "╨а╨Ъ 1", "╨а╨Ъ2": "╨а╨Ъ 2", "╨а╨Ъ3": "╨а╨Ъ 3",
    "rk1": "╨а╨Ъ 1", "rk2": "╨а╨Ъ 2", "rk3": "╨а╨Ъ 3",
    "╨а╨Ъ-1": "╨а╨Ъ 1", "╨а╨Ъ-2": "╨а╨Ъ 2", "╨а╨Ъ-3": "╨а╨Ъ 3",
}

# ---------------------------------------------------------------------------
# ╨Ь╨╛╨┤╨╡╨╗╤М ╨┤╨░╨╜╨╜╤Л╤Е
# ---------------------------------------------------------------------------


@dataclass
class Row:
    """╨Ю╨┤╨╜╨░ ╤Б╤В╤А╨╛╨║╨░ ╨┐╤А╨╕╨▓╨╡╨┤╤С╨╜╨╜╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е."""
    source: str
    campaign: str
    date: str          # DD.MM.YY
    impressions: int
    clicks: int
    cost_rub: float


# ---------------------------------------------------------------------------
# ╨Т╤Б╨┐╨╛╨╝╨╛╨│╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╤Д╤Г╨╜╨║╤Ж╨╕╨╕ ╨┐╨░╤А╤Б╨╕╨╜╨│╨░
# ---------------------------------------------------------------------------


def _parse_int_ru(value: str) -> int:
    """╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╤Ж╨╡╨╗╨╛╨╡ ╤З╨╕╤Б╨╗╨╛ ╨▓ ╤А╤Г╤Б╤Б╨║╨╛╨╣ ╨╗╨╛╨║╨░╨╗╨╕ (╨┐╤А╨╛╨▒╨╡╨╗ ╨║╨░╨║ ╤А╨░╨╖╨┤╨╡╨╗╨╕╤В╨╡╨╗╤М ╤В╤Л╤Б╤П╤З)."""
    return int(value.replace(" ", "").replace("\u00a0", ""))


def _parse_float_ru(value: str) -> float:
    """╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╨┤╤А╨╛╨▒╨╜╨╛╨╡ ╤З╨╕╤Б╨╗╨╛ ╨▓ ╤А╤Г╤Б╤Б╨║╨╛╨╣ ╨╗╨╛╨║╨░╨╗╨╕ (╨┐╤А╨╛╨▒╨╡╨╗-╤А╨░╨╖╨┤╨╡╨╗╨╕╤В╨╡╨╗╤М ╤В╤Л╤Б╤П╤З, ╨╖╨░╨┐╤П╤В╨░╤П ╨║╨░╨║ ╨┤╨╡╤Б╤П╤В╨╕╤З╨╜╤Л╨╣ ╤А╨░╨╖╨┤╨╡╨╗╨╕╤В╨╡╨╗╤М)."""
    cleaned = value.strip()
    # ╨г╨┤╨░╨╗╨╕╤В╤М ╤Б╨╕╨╝╨▓╨╛╨╗ ╨▓╨░╨╗╤О╤В╤Л ╨╕ ╨╜╨╡╤А╨░╨╖╤А╤Л╨▓╨╜╤Л╨╣ ╨┐╤А╨╛╨▒╨╡╨╗
    cleaned = cleaned.replace("тВ╜", "").replace("\u00a0", "").strip()
    # ╨г╨┤╨░╨╗╨╕╤В╤М ╨┐╤А╨╛╨▒╨╡╨╗╤Л (╤А╨░╨╖╨┤╨╡╨╗╨╕╤В╨╡╨╗╨╕ ╤В╤Л╤Б╤П╤З)
    cleaned = cleaned.replace(" ", "")
    # ╨Ч╨░╨╝╨╡╨╜╨╕╤В╤М ╨┤╨╡╤Б╤П╤В╨╕╤З╨╜╤Г╤О ╨╖╨░╨┐╤П╤В╤Г╤О ╨╜╨░ ╤В╨╛╤З╨║╤Г
    cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _parse_date_sheet2(date_str: str) -> str:
    """╨Я╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╤В╤М ╨У╨У-╨Ь╨Ь-╨Ф╨Ф тЖТ ╨Ф╨Ф.╨Ь╨Ь.╨У╨У."""
    # date_str, ╨╜╨░╨┐╤А╨╕╨╝╨╡╤А "24-03-01"
    parts = date_str.strip().split("-")
    if len(parts) != 3:
        return date_str
    yy, mm, dd = parts
    return f"{dd}.{mm}.{yy}"


def _parse_date_sheet3(date_str: str) -> str:
    """╨Я╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╤В╤М '╨Ь╨░╤А╤В 2024, 1' тЖТ ╨Ф╨Ф.╨Ь╨Ь.╨У╨У."""
    # ╨г╨┤╨░╨╗╨╕╤В╤М ╨║╨░╨▓╤Л╤З╨║╨╕, ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М
    date_str = date_str.strip().strip('"')
    # ╨и╨░╨▒╨╗╨╛╨╜: "╨Ь╨░╤А╤В 2024, 1" тАФ ╨╝╨╡╤Б╤П╤Ж ╨│╨╛╨┤, ╨┤╨╡╨╜╤М
    match = re.match(r"(\D+)\s+(\d{4}),\s*(\d+)", date_str)
    if not match:
        return date_str
    month_name, year, day = match.groups()
    month_name = month_name.strip().lower()
    month_num = RUSSIAN_MONTHS.get(month_name, "??")
    yy = year[2:]  # 2024 тЖТ 24
    return f"{int(day):02d}.{month_num}.{yy}"


def _normalise_campaign(name: str) -> str:
    """╨Я╤А╨╕╨▓╨╡╤Б╤В╨╕ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨║╨░╨╝╨┐╨░╨╜╨╕╨╕ ╨║ ╨║╨░╨╜╨╛╨╜╨╕╤З╨╡╤Б╨║╨╛╨╝╤Г ╨▓╨╕╨┤╤Г."""
    return CANONICAL_CAMPAIGNS.get(name.strip(), name.strip())


def _read_csv_rows(path: Path, source: str, date_parser_func) -> List[Row]:
    """╨Ю╨▒╤Й╨╕╨╣ CSV-╤З╨╕╤В╨░╤В╨╡╨╗╤М ╨┤╨╗╤П ╤Д╨╛╤А╨╝╨░╤В╨░ ╨Ы╨╕╤Б╤В1/╨Ы╨╕╤Б╤В2 (╨║╨╛╨╗╨╛╨╜╨║╨╕: ╨Ф╨░╤В╨░, ╨а╨Ъ, ╨Я╨╛╨║╨░╨╖╤Л, ╨Ъ╨╗╨╕╨║╨╕, ╨Ч╨░╤В╤А╨░╤В╤Л, ╤А╤Г╨▒)."""
    rows: List[Row] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = date_parser_func(line["╨Ф╨░╤В╨░"])
            campaign = _normalise_campaign(line["╨а╨Ъ"])
            impressions = _parse_int_ru(line["╨Я╨╛╨║╨░╨╖╤Л"])
            clicks = _parse_int_ru(line["╨Ъ╨╗╨╕╨║╨╕"])
            cost = _parse_float_ru(line["╨Ч╨░╤В╤А╨░╤В╤Л, ╤А╤Г╨▒"])
            rows.append(Row(source, campaign, date, impressions, clicks, cost))
    return rows


# ---------------------------------------------------------------------------
# ╨Я╨░╤А╤Б╨╡╤А╤Л ╨┐╨╛ ╨╗╨╕╤Б╤В╨░╨╝
# ---------------------------------------------------------------------------


def parse_sheet1(path: Path) -> List[Row]:
    """
    ╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╨Ы╨╕╤Б╤В1.

    ╨д╨╛╤А╨╝╨░╤В: ╨Ф╨Ф.╨Ь╨Ь.╨У╨У, ╨а╨Ъ1/╨а╨Ъ2/╨а╨Ъ3, ╤Ж╨╡╨╗╤Л╨╡ ╤З╨╕╤Б╨╗╨░ ╨▓ ╤А╤Г╤Б╤Б╨║╨╛╨╣ ╨╗╨╛╨║╨░╨╗╨╕
    ╤Б ╨┐╤А╨╛╨▒╨╡╨╗╨╛╨╝-╤А╨░╨╖╨┤╨╡╨╗╨╕╤В╨╡╨╗╨╡╨╝ ╤В╤Л╤Б╤П╤З. ╨а╨░╤Б╤Е╨╛╨┤╤Л ╨▓ ╤А╤Г╨▒.
    """
    return _read_csv_rows(path, "╨Ы╨╕╤Б╤В1", lambda d: d.strip())


def parse_sheet2(path: Path) -> List[Row]:
    """
    ╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╨Ы╨╕╤Б╤В2.

    ╨д╨╛╤А╨╝╨░╤В: ╨У╨У-╨Ь╨Ь-╨Ф╨Ф, rk1/rk2/rk3, ╤Ж╨╡╨╗╤Л╨╡ ╤З╨╕╤Б╨╗╨░ ╨▒╨╡╨╖ ╤Д╨╛╤А╨╝╨░╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П.
    ╨а╨░╤Б╤Е╨╛╨┤╤Л ╨▓ ╤А╤Г╨▒ ╨▓ ╤А╤Г╤Б╤Б╨║╨╛╨╣ ╨╗╨╛╨║╨░╨╗╨╕: "3 492,00 тВ╜".
    """
    return _read_csv_rows(path, "╨Ы╨╕╤Б╤В2", _parse_date_sheet2)


def parse_sheet3(path: Path) -> List[Row]:
    """
    ╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╨Ы╨╕╤Б╤В3.

    ╨д╨╛╤А╨╝╨░╤В:
      - ╨Ф╨░╤В╨░: "╨Ь╨░╤А╤В 2024, 1" тЖТ 01.03.24
      - ╨Ъ╨░╨╝╨┐╨░╨╜╨╕╤П: ╨а╨Ъ-1/╨а╨Ъ-2/╨а╨Ъ-3
      - ╨Я╨╛╨║╨░╨╖╤Л ╨▓ ╤В╤Л╤Б╤П╤З╨░╤Е (╨║╨╛╨╗╨╛╨╜╨║╨░: "╨Я╨╛╨║╨░╨╖╤Л, ╤В╤Л╤Б.") тЖТ ├Ч1000
      - ╨а╨░╤Б╤Е╨╛╨┤╤Л ╨▓ USD (╨║╨╛╨╗╨╛╨╜╨║╨░: "╨Ч╨░╤В╤А╨░╤В╤Л, $") тЖТ ├Ч USD_TO_RUB
    """
    rows: List[Row] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = _parse_date_sheet3(line["╨Ф╨░╤В╨░"])
            campaign = _normalise_campaign(line["╨а╨Ъ"])
            # ╨Я╨╛╨║╨░╨╖╤Л ╤Г╨║╨░╨╖╨░╨╜╤Л ╨▓ ╤В╤Л╤Б╤П╤З╨░╤Е
            impressions_raw = _parse_float_ru(line["╨Я╨╛╨║╨░╨╖╤Л, ╤В╤Л╤Б."])
            impressions = int(round(impressions_raw * 1000))
            clicks = _parse_int_ru(line["╨Ъ╨╗╨╕╨║╨╕"])
            cost_usd = _parse_float_ru(line["╨Ч╨░╤В╤А╨░╤В╤Л, $"])
            cost_rub = round(cost_usd * USD_TO_RUB, 2)
            rows.append(Row("╨Ы╨╕╤Б╤В3", campaign, date, impressions, clicks, cost_rub))
    return rows


# ---------------------------------------------------------------------------
# ╨Т╤Б╨┐╨╛╨╝╨╛╨│╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╤Д╤Г╨╜╨║╤Ж╨╕╨╕ ╨▓╤Л╨▓╨╛╨┤╨░
# ---------------------------------------------------------------------------


def print_table(rows: List[Row]) -> None:
    """╨Т╤Л╨▓╨╡╤Б╤В╨╕ ╨╡╨┤╨╕╨╜╤Г╤О ╤В╨░╨▒╨╗╨╕╤Ж╤Г."""
    header = f"{'╨Ш╤Б╤В╨╛╤З╨╜╨╕╨║':<8} {'╨Ъ╨░╨╝╨┐╨░╨╜╨╕╤П':<8} {'╨Ф╨░╤В╨░':<10} {'╨Я╨╛╨║╨░╨╖╤Л':>10} {'╨Ъ╨╗╨╕╨║╨╕':>8} {'╨Ч╨░╤В╤А╨░╤В╤Л, ╤А╤Г╨▒':>14}"
    sep = "-" * len(header)
    print_header_block(
        title="╨Ю╨▒╤К╨╡╨┤╨╕╨╜╤С╨╜╨╜╤Л╨╣ ╨╛╤В╤З╤С╤В ╨┐╨╛ ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╨░╨╝",
        description="╨Ъ╨╛╨╜╤Б╨╛╨╗╨╕╨┤╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╖ ╨п╨╜╨┤╨╡╨║╤Б.╨Ф╨╕╤А╨╡╨║╤В, VK ╨а╨╡╨║╨╗╨░╨╝╨░ ╨╕ SberAds тАФ ╨║╨░╨╝╨┐╨░╨╜╨╕╤П, ╨┤╨░╤В╨░, ╨┐╨╛╨║╨░╨╖╤Л, ╨║╨╗╨╕╨║╨╕, ╨╖╨░╤В╤А╨░╤В╤Л",
        period="╨Т╨╡╤Б╤М ╨┐╨╡╤А╨╕╨╛╨┤ ╨┤╨░╨╜╨╜╤Л╤Е",
    )
    print(header)
    print(sep)
    for r in rows:
        print(
            f"{r.source:<8} {r.campaign:<8} {r.date:<10} "
            f"{r.impressions:>10,} {r.clicks:>8,} {r.cost_rub:>14.2f}"
        )
    print(sep)
    totals = _totals(rows)
    print(
        f"{'╨Ш╨в╨Ю╨У╨Ю':<8} {'':<8} {'':<10} "
        f"{totals.impressions:>10,} {totals.clicks:>8,} {totals.cost_rub:>14.2f}"
    )
    print("=" * len(header))


def _totals(rows: List[Row]) -> Row:
    """╨б╤Г╨╝╨╝╨╕╤А╨╛╨▓╨░╤В╤М ╨┐╨╛╨║╨░╨╖╨░╤В╨╡╨╗╨╕ ╨┐╨╛ ╨▓╤Б╨╡╨╝ ╤Б╤В╤А╨╛╨║╨░╨╝."""
    return Row(
        source="TOTAL",
        campaign="",
        date="",
        impressions=sum(r.impressions for r in rows),
        clicks=sum(r.clicks for r in rows),
        cost_rub=sum(r.cost_rub for r in rows),
    )


def _print_metrics_line(label: str, impressions: int, clicks: int, cost_rub: float) -> None:
    """╨Т╤Л╨▓╨╡╤Б╤В╨╕ ╨▒╨╗╨╛╨║ ╨╕╨╖ 5 ╤Б╤В╤А╨╛╨║ ╤Б ╨╝╨╡╤В╤А╨╕╨║╨░╨╝╨╕ (╨Я╨╛╨║╨░╨╖╤Л, ╨Ъ╨╗╨╕╨║╨╕, ╨Ч╨░╤В╤А╨░╤В╤Л, CTR, CPM) ╨┤╨╗╤П ╤Г╨║╨░╨╖╨░╨╜╨╜╨╛╨╣ ╨╝╨╡╤В╨║╨╕."""
    ctr = (clicks / impressions * 100) if impressions else 0.0
    cpm = (cost_rub / impressions * 1000) if impressions else 0.0
    print(f"  ╨Я╨╛╨║╨░╨╖╤Л      : {impressions:>12,}")
    print(f"  ╨Ъ╨╗╨╕╨║╨╕       : {clicks:>12,}")
    print(f"  ╨Ч╨░╤В╤А╨░╤В╤Л, ╤А╤Г╨▒: {cost_rub:>12.2f}")
    print(f"  CTR, %      : {ctr:>11.4f}")
    print(f"  CPM, ╤А╤Г╨▒    : {cpm:>11.2f}")


def _print_source_summary(source: str, rows: List[Row],
                          grand_total: Row) -> None:
    """╨Т╤Л╨▓╨╡╤Б╤В╨╕ ╤Б╨▓╨╛╨┤╨║╤Г ╨┐╨╛ ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╤Г ╨╕ ╨╜╨░╨║╨╛╨┐╨╕╤В╤М ╨▓ grand_total."""
    imp = sum(r.impressions for r in rows)
    clk = sum(r.clicks for r in rows)
    cst = sum(r.cost_rub for r in rows)
    print(f"\n{source}:")
    print(f"  ╨б╤В╤А╨╛╨║       : {len(rows)}")
    _print_metrics_line(source, imp, clk, cst)
    grand_total.impressions += imp
    grand_total.clicks += clk
    grand_total.cost_rub += cst


def _print_grand_total(grand_total: Row) -> None:
    """╨Т╤Л╨▓╨╡╤Б╤В╨╕ ╨╛╨▒╤Й╨╕╨╣ ╨╕╤В╨╛╨│ ╤Б ╨┤╨╛╨┐╤Г╤Й╨╡╨╜╨╕╤П╨╝╨╕."""
    print_header_block(
        title="╨Ю╨▒╤Й╨╕╨╣ ╨╕╤В╨╛╨│",
        description="╨У╤А╨░╨╜╨┤-╤В╨╛╤В╨░╨╗ ╨┐╨╛ ╨▓╤Б╨╡╨╝ ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╨░╨╝: ╤Б╤Г╨╝╨╝╨░╤А╨╜╤Л╨╡ ╨┐╨╛╨║╨░╨╖╤Л, ╨║╨╗╨╕╨║╨╕ ╨╕ ╨╖╨░╤В╤А╨░╤В╤Л",
        period="╨Т╨╡╤Б╤М ╨┐╨╡╤А╨╕╨╛╨┤ ╨┤╨░╨╜╨╜╤Л╤Е",
    )
    _print_metrics_line("GRAND TOTAL", grand_total.impressions,
                        grand_total.clicks, grand_total.cost_rub)
    print(f"\n{' ╨Ф╨╛╨┐╤Г╤Й╨╡╨╜╨╕╤П ':-^70}")
    print(f"  ╨Ъ╤Г╤А╤Б ╨Ы╨╕╤Б╤В3 USD -> RUB: {USD_TO_RUB:.0f} ╤А╤Г╨▒/$ (╨┐╤А╨╕╨▒╨╗╨╕╨╖╨╕╤В╨╡╨╗╤М╨╜╨╛ Q1 2024)")


def print_summary(rows_by_source: Dict[str, List[Row]]) -> None:
    """╨Т╤Л╨▓╨╡╤Б╤В╨╕ ╤Б╨▓╨╛╨┤╨║╤Г ╨┐╨╛ ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╨░╨╝."""
    print_header_block(
        title="╨б╨▓╨╛╨┤╨║╨░ ╨┐╨╛ ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╨░╨╝",
        description="╨б╤Г╨╝╨╝╨░╤А╨╜╤Л╨╡ ╨┐╨╛╨║╨░╨╖╤Л, ╨║╨╗╨╕╨║╨╕ ╨╕ ╨╖╨░╤В╤А╨░╤В╤Л ╨┐╨╛ ╨║╨░╨╢╨┤╨╛╨╝╤Г ╨╕╤Б╤В╨╛╤З╨╜╨╕╨║╤Г ╨┤╨░╨╜╨╜╤Л╤Е ╨╖╨░ ╨▓╨╡╤Б╤М ╨┐╨╡╤А╨╕╨╛╨┤",
        period="╨Т╨╡╤Б╤М ╨┐╨╡╤А╨╕╨╛╨┤ ╨┤╨░╨╜╨╜╤Л╤Е",
    )

    grand_total = Row("", "", "", 0, 0, 0.0)

    for source in ["╨Ы╨╕╤Б╤В1", "╨Ы╨╕╤Б╤В2", "╨Ы╨╕╤Б╤В3"]:
        srows = rows_by_source.get(source, [])
        _print_source_summary(source, srows, grand_total)

    _print_grand_total(grand_total)


# ---------------------------------------------------------------------------
# ╨н╨║╤Б╨┐╨╛╤А╤В ╨▓ CSV
# ---------------------------------------------------------------------------


def export_csv(rows: List[Row], path: Path) -> None:
    """╨н╨║╤Б╨┐╨╛╤А╤В╨╕╤А╨╛╨▓╨░╤В╤М ╨╛╨▒╤К╨╡╨┤╨╕╨╜╤С╨╜╨╜╤Л╨╡ ╤Б╤В╤А╨╛╨║╨╕ ╨▓ CSV-╤Д╨░╨╣╨╗ (UTF-8 BOM, ╨┐╨╡╤А╨╡╨╖╨░╨┐╨╕╤Б╤М)."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Campaign", "Date", "Impressions", "Clicks", "Cost_RUB"])
        for r in rows:
            writer.writerow([
                r.source,
                r.campaign,
                r.date,
                r.impressions,
                r.clicks,
                f"{r.cost_rub:.2f}",
            ])


# ---------------------------------------------------------------------------
# ╨У╨╗╨░╨▓╨╜╨░╤П
# ---------------------------------------------------------------------------


def main() -> None:
    """╨а╨░╨╖╨╛╨▒╤А╨░╤В╤М ╨▓╤Б╨╡ 3 CSV-╤Д╨░╨╣╨╗╨░, ╨┐╤А╨╕╨▓╨╡╤Б╤В╨╕ ╨║ ╨╡╨┤╨╕╨╜╨╛╨╝╤Г ╤Д╨╛╤А╨╝╨░╤В╤Г, ╨▓╤Л╨▓╨╡╤Б╤В╨╕ ╨╛╨▒╤К╨╡╨┤╨╕╨╜╤С╨╜╨╜╤Г╤О ╤В╨░╨▒╨╗╨╕╤Ж╤Г + ╤Б╨▓╨╛╨┤╨║╤Г."""
    parsers = {
        "╨Ы╨╕╤Б╤В1": parse_sheet1,
        "╨Ы╨╕╤Б╤В2": parse_sheet2,
        "╨Ы╨╕╤Б╤В3": parse_sheet3,
    }

    all_rows: List[Row] = []
    rows_by_source: Dict[str, List[Row]] = {}

    for source, parser in parsers.items():
        path = FILES[source]
        if not path.exists():
            print(f"тЪа  ╨д╨░╨╣╨╗ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜: {path}")
            continue
        rows = parser(path)
        rows_by_source[source] = rows
        all_rows.extend(rows)

    # ╨б╨╛╤А╤В╨╕╤А╨╛╨▓╨║╨░ ╨┐╨╛ ╨┤╨░╤В╨╡, ╨╖╨░╤В╨╡╨╝ ╨┐╨╛ ╨║╨░╨╝╨┐╨░╨╜╨╕╨╕
    all_rows.sort(key=lambda r: (r.date, r.campaign))

    # ╨н╨║╤Б╨┐╨╛╤А╤В ╨▓ CSV ╨┐╨╡╤А╨╡╨┤ ╨▓╤Л╨▓╨╛╨┤╨╛╨╝ ╨▓ ╨║╨╛╨╜╤Б╨╛╨╗╤М
    export_csv(all_rows, BASE_DIR / "consolidated_report.csv")

    print_table(all_rows)
    print_summary(rows_by_source)


if __name__ == "__main__":
    main()
