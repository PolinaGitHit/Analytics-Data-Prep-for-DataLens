"""
task3_consolidate.py — Task 3: Consolidate 3 CSV exports from different ad networks.

Reads 3 CSV files (Лист1, Лист2, Лист3) each in a different format,
parses and normalises them into a unified report, then prints the result.

Assumptions:
  - Лист3 costs are in USD; exchange rate ~90 руб/$ (documented inline).
  - Canonical campaign names: "РК 1", "РК 2", "РК 3".
  - Unified date format: DD.MM.YY (consistent with input sources).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

FILES: Dict[str, Path] = {
    "Лист1": BASE_DIR / "Тестовое маркетологу 2024, задача 3 - Лист1.csv",
    "Лист2": BASE_DIR / "Тестовое маркетологу 2024, задача 3 - Лист2.csv",
    "Лист3": BASE_DIR / "Тестовое маркетологу 2024, задача 3 - Лист3.csv",
}

# Exchange rate assumption: 1 USD ≈ 90 RUB (Q1 2024 approximate rate)
USD_TO_RUB = 90.0

# Month name mapping for Лист3 date format ("Март 2024, 1")
RUSSIAN_MONTHS: Dict[str, str] = {
    "январь": "01", "января": "01",
    "февраль": "02", "февраля": "02",
    "март": "03", "марта": "03",
    "апрель": "04", "апреля": "04",
    "май": "05", "мая": "05",
    "июнь": "06", "июня": "06",
    "июль": "07", "июля": "07",
    "август": "08", "августа": "08",
    "сентябрь": "09", "сентября": "09",
    "октябрь": "10", "октября": "10",
    "ноябрь": "11", "ноября": "11",
    "декабрь": "12", "декабря": "12",
}

# Mapping from source campaign names to canonical
CANONICAL_CAMPAIGNS: Dict[str, str] = {
    "РК1": "РК 1", "РК2": "РК 2", "РК3": "РК 3",
    "rk1": "РК 1", "rk2": "РК 2", "rk3": "РК 3",
    "РК-1": "РК 1", "РК-2": "РК 2", "РК-3": "РК 3",
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Row:
    """A single normalised data row."""
    source: str
    campaign: str
    date: str          # DD.MM.YY
    impressions: int
    clicks: int
    cost_rub: float


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_int_ru(value: str) -> int:
    """Parse a Russian-locale integer (spaces as thousands separators)."""
    return int(value.replace(" ", "").replace("\u00a0", ""))


def _parse_float_ru(value: str) -> float:
    """Parse a Russian-locale float (space thousands, comma decimal)."""
    cleaned = value.strip()
    # Remove currency symbol and non-breaking space
    cleaned = cleaned.replace("₽", "").replace("\u00a0", "").strip()
    # Remove spaces (thousands separators)
    cleaned = cleaned.replace(" ", "")
    # Replace comma decimal with dot
    cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _parse_date_sheet2(date_str: str) -> str:
    """Convert YY-MM-DD → DD.MM.YY."""
    # date_str e.g. "24-03-01"
    parts = date_str.strip().split("-")
    if len(parts) != 3:
        return date_str
    yy, mm, dd = parts
    return f"{dd}.{mm}.{yy}"


def _parse_date_sheet3(date_str: str) -> str:
    """Convert 'Март 2024, 1' → DD.MM.YY."""
    # Strip quotes if present
    date_str = date_str.strip().strip('"')
    # Pattern: "Март 2024, 1" — month year, day
    match = re.match(r"(\D+)\s+(\d{4}),\s*(\d+)", date_str)
    if not match:
        return date_str
    month_name, year, day = match.groups()
    month_name = month_name.strip().lower()
    month_num = RUSSIAN_MONTHS.get(month_name, "??")
    yy = year[2:]  # 2024 → 24
    return f"{int(day):02d}.{month_num}.{yy}"


def _normalise_campaign(name: str) -> str:
    """Map source campaign name to canonical form."""
    return CANONICAL_CAMPAIGNS.get(name.strip(), name.strip())


def _read_csv_rows(path: Path, source: str, date_parser_func) -> List[Row]:
    """Shared CSV reader for Лист1/Лист2 format (columns: Дата, РК, Показы, Клики, Затраты, руб)."""
    rows: List[Row] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = date_parser_func(line["Дата"])
            campaign = _normalise_campaign(line["РК"])
            impressions = _parse_int_ru(line["Показы"])
            clicks = _parse_int_ru(line["Клики"])
            cost = _parse_float_ru(line["Затраты, руб"])
            rows.append(Row(source, campaign, date, impressions, clicks, cost))
    return rows


# ---------------------------------------------------------------------------
# Parsers per sheet
# ---------------------------------------------------------------------------


def parse_sheet1(path: Path) -> List[Row]:
    """
    Parse Лист1.

    Format: DD.MM.YY, РК1/РК2/РК3, Russian-locale integers with space
    thousands separators. Cost in руб.
    """
    return _read_csv_rows(path, "Лист1", lambda d: d.strip())


def parse_sheet2(path: Path) -> List[Row]:
    """
    Parse Лист2.

    Format: YY-MM-DD, rk1/rk2/rk3, plain integers.
    Cost in руб with Russian locale: "3 492,00 ₽".
    """
    return _read_csv_rows(path, "Лист2", _parse_date_sheet2)


def parse_sheet3(path: Path) -> List[Row]:
    """
    Parse Лист3.

    Format:
      - Date: "Март 2024, 1" → 01.03.24
      - Campaign: РК-1/РК-2/РК-3
      - Impressions in thousands (column: "Показы, тыс.") → ×1000
      - Cost in USD (column: "Затраты, $") → × USD_TO_RUB
    """
    rows: List[Row] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = _parse_date_sheet3(line["Дата"])
            campaign = _normalise_campaign(line["РК"])
            # Impressions are in thousands
            impressions_raw = _parse_float_ru(line["Показы, тыс."])
            impressions = int(round(impressions_raw * 1000))
            clicks = _parse_int_ru(line["Клики"])
            cost_usd = _parse_float_ru(line["Затраты, $"])
            cost_rub = round(cost_usd * USD_TO_RUB, 2)
            rows.append(Row("Лист3", campaign, date, impressions, clicks, cost_rub))
    return rows


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------


def print_table(rows: List[Row]) -> None:
    """Print the unified table."""
    header = f"{'Source':<8} {'Campaign':<8} {'Date':<10} {'Показы':>10} {'Клики':>8} {'Затраты, руб':>14}"
    sep = "-" * len(header)
    print("\n" + "=" * len(header))
    print("UNIFIED REPORT")
    print("=" * len(header))
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
        f"{'TOTAL':<8} {'':<8} {'':<10} "
        f"{totals.impressions:>10,} {totals.clicks:>8,} {totals.cost_rub:>14.2f}"
    )
    print("=" * len(header))


def _totals(rows: List[Row]) -> Row:
    """Aggregate totals across all rows."""
    return Row(
        source="TOTAL",
        campaign="",
        date="",
        impressions=sum(r.impressions for r in rows),
        clicks=sum(r.clicks for r in rows),
        cost_rub=sum(r.cost_rub for r in rows),
    )


def _print_metrics_line(label: str, impressions: int, clicks: int, cost_rub: float) -> None:
    """Print the 5-line metrics block (Показы, Клики, Затраты, CTR, CPM) for a label."""
    ctr = (clicks / impressions * 100) if impressions else 0.0
    cpm = (cost_rub / impressions * 1000) if impressions else 0.0
    print(f"  Показы      : {impressions:>12,}")
    print(f"  Клики       : {clicks:>12,}")
    print(f"  Затраты, руб: {cost_rub:>12.2f}")
    print(f"  CTR, %      : {ctr:>11.4f}")
    print(f"  CPM, руб    : {cpm:>11.2f}")


def _print_source_summary(source: str, rows: List[Row],
                          grand_total: Row) -> None:
    """Print per-source summary block and accumulate into grand_total."""
    imp = sum(r.impressions for r in rows)
    clk = sum(r.clicks for r in rows)
    cst = sum(r.cost_rub for r in rows)
    print(f"\n{source}:")
    print(f"  Rows        : {len(rows)}")
    _print_metrics_line(source, imp, clk, cst)
    grand_total.impressions += imp
    grand_total.clicks += clk
    grand_total.cost_rub += cst


def _print_grand_total(grand_total: Row) -> None:
    """Print grand total block with assumptions."""
    print(f"\n{' GRAND TOTAL ':-^70}")
    _print_metrics_line("GRAND TOTAL", grand_total.impressions,
                        grand_total.clicks, grand_total.cost_rub)
    print(f"\n{' Assumptions ':-^70}")
    print(f"  Лист3 USD -> RUB exchange rate: {USD_TO_RUB:.0f} руб/$ (approximate Q1 2024 rate)")


def print_summary(rows_by_source: Dict[str, List[Row]]) -> None:
    """Print per-source summary."""
    print("\n" + "=" * 70)
    print("CROSS-SOURCE SUMMARY")
    print("=" * 70)

    grand_total = Row("", "", "", 0, 0, 0.0)

    for source in ["Лист1", "Лист2", "Лист3"]:
        srows = rows_by_source.get(source, [])
        _print_source_summary(source, srows, grand_total)

    _print_grand_total(grand_total)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def export_csv(rows: List[Row], path: Path) -> None:
    """Export unified rows to a CSV file (UTF-8 BOM, overwrite)."""
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
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse all 3 CSV files, normalise, print consolidated table + summary."""
    parsers = {
        "Лист1": parse_sheet1,
        "Лист2": parse_sheet2,
        "Лист3": parse_sheet3,
    }

    all_rows: List[Row] = []
    rows_by_source: Dict[str, List[Row]] = {}

    for source, parser in parsers.items():
        path = FILES[source]
        if not path.exists():
            print(f"⚠  File not found: {path}")
            continue
        rows = parser(path)
        rows_by_source[source] = rows
        all_rows.extend(rows)

    # Sort by date then campaign
    all_rows.sort(key=lambda r: (r.date, r.campaign))

    # Export to CSV before console output
    export_csv(all_rows, BASE_DIR / "consolidated_report.csv")

    print_table(all_rows)
    print_summary(rows_by_source)


if __name__ == "__main__":
    main()