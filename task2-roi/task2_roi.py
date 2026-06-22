"""Задача 2: Вычислить ROI кампании с 6-недельной воронкой LTV.

Читает CSV-данные за 14 дней, вычисляет воронку посетитель→покупатель по дням,
суммирует выручку по всем дням и выводит ROI.
"""

import csv
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from print_utils import print_header_block


class FunnelRow(NamedTuple):
    """Строка воронки: день, затраты, метрики и LTV."""

    day: str
    cost: float
    cpm: float
    ctr_pct: float
    cr_reg_pct: float
    cr_buy_pct: float
    ltv: float


def _parse_float(s: str) -> float:
    """Преобразовать значение ячейки CSV в float, обрабатывая запятую как десятичный разделитель."""
    return float(s.strip().replace(",", "."))


def parse_csv(path: str) -> list[FunnelRow]:
    """Разобрать CSV задачи 2, обрабатывая десятичные разделители-запятые."""
    rows: list[FunnelRow] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # пропустить заголовок
        for line in reader:
            if not line:
                continue
            day = line[0].strip()
            cost = _parse_float(line[1])
            cpm = _parse_float(line[2])
            ctr_pct = _parse_float(line[3])
            cr_reg_pct = _parse_float(line[4])
            cr_buy_pct = _parse_float(line[5])
            ltv = _parse_float(line[6])
            rows.append(FunnelRow(day, cost, cpm, ctr_pct, cr_reg_pct, cr_buy_pct, ltv))
    return rows


def compute_funnel(rows: list[FunnelRow]) -> list[dict]:
    """Вычислить ежедневные метрики воронки для каждой строки."""
    results: list[dict] = []
    for r in rows:
        impressions = r.cost / r.cpm * 1000.0
        clicks = impressions * r.ctr_pct / 100.0
        registrations = impressions * r.cr_reg_pct / 100.0
        buyers = registrations * r.cr_buy_pct / 100.0
        revenue = buyers * r.ltv
        results.append({
            "day": r.day,
            "cost": r.cost,
            "cpm": r.cpm,
            "ctr_pct": r.ctr_pct,
            "cr_reg_pct": r.cr_reg_pct,
            "cr_buy_pct": r.cr_buy_pct,
            "ltv": r.ltv,
            "impressions": impressions,
            "clicks": clicks,
            "registrations": registrations,
            "buyers": buyers,
            "revenue": revenue,
        })
    return results


def print_daily_table(results: list[dict]) -> None:
    """Вывести форматированную ежедневную таблицу со всеми промежуточными метриками."""
    print_header_block(
        title="Ежедневная воронка LTV и выручки",
        description="Затраты, CPM, CTR, конверсия регистраций и покупок, LTV, показы, клики, регистрации, покупки, выручка по дням",
        period="По дням кампании (14 дней)",
    )
    header = (
        f"{'День':<8} {'Затраты':>10} {'CPM':>9} {'CTR%':>7} {'CR.reg%':>9} "
        f"{'CR.buy%':>9} {'LTV':>9} {'Показы':>12} {'Клики':>10} "
        f"{'Регистр.':>8} {'Покуп.':>8} {'Выручка':>12}"
    )
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for r in results:
        print(
            f"{r['day']:<8} {r['cost']:>10,.0f} {r['cpm']:>9,.1f} "
            f"{r['ctr_pct']:>7,.2f} {r['cr_reg_pct']:>9,.2f} "
            f"{r['cr_buy_pct']:>9,.2f} {r['ltv']:>9,.0f} "
            f"{r['impressions']:>12,.0f} {r['clicks']:>10,.0f} "
            f"{r['registrations']:>8,.1f} {r['buyers']:>8,.1f} "
            f"{r['revenue']:>12,.0f}"
        )
    print(sep)


def print_summary(results: list[dict]) -> None:
    """Вывести итоги и ROI."""
    total_cost = sum(r["cost"] for r in results)
    total_impressions = sum(r["impressions"] for r in results)
    total_clicks = sum(r["clicks"] for r in results)
    total_registrations = sum(r["registrations"] for r in results)
    total_buyers = sum(r["buyers"] for r in results)
    total_revenue = sum(r["revenue"] for r in results)
    roi_pct = (total_revenue - total_cost) / total_cost * 100.0

    print_header_block(
        title="Сводные итоги ROI",
        description="Итоговые метрики за весь период: суммарные затраты, показы, клики, регистрации, покупки, выручка, ROI",
        period="За весь период кампании (14 дней)",
    )
    print(f"{'Всего затрат (руб):':<25} {total_cost:>12,.0f}")
    print(f"{'Всего показов:':<25} {total_impressions:>12,.0f}")
    print(f"{'Всего кликов:':<25} {total_clicks:>12,.0f}")
    print(f"{'Всего регистраций:':<25} {total_registrations:>12,.1f}")
    print(f"{'Всего покупателей:':<25} {total_buyers:>12,.1f}")
    print(f"{'Всего выручки (руб):':<25} {total_revenue:>12,.0f}")
    print(f"{'ROI (%):':<25} {roi_pct:>12,.2f}")
    print(f"{'=' * 50}")
    if roi_pct > 0:
        print("Кампания ПРИБЫЛЬНА.")
    else:
        print("Кампания НЕПРИБЫЛЬНА.")


def main() -> None:
    """Точка входа для скрипта вычисления ROI.

    Читает путь к CSV из первого аргумента командной строки, разбирает данные,
    вычисляет метрики воронки и выводит ежедневную таблицу и сводку с ROI.

    Args:
        Нет, помимо аргументов командной строки (обрабатываются через sys.argv).

    Returns:
        None
    """
    if len(sys.argv) < 2:
        print("Использование: python task2_roi.py <путь_к_csv>", file=sys.stderr)
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"Файл не найден: {csv_path}", file=sys.stderr)
        sys.exit(1)

    rows = parse_csv(csv_path)
    print(f"Загружено {len(rows)} дней данных\n")

    results = compute_funnel(rows)
    print_daily_table(results)
    print_summary(results)


if __name__ == "__main__":
    main()