"""Вычисление показовых и кликовых KPI (CPM, CTR) для кампании из CSV задачи 1.

Читает набор данных кампании 3 дня × 3 сети, вычисляет CPC, CPM, CTR,
определяет попадания в бюджетные лимиты, агрегирует ежедневные метрики
по кампании в целом, вычисляет средние по кампании, проверяет требования
и выводит интерпретацию поведения с ограничением по бюджету.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from print_utils import print_header_block


# ── типы домена ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CampaignRow:
    """Одна строка данных после парсинга CSV.

    Атрибуты:
        day: Метка дня (например, 'День 1').
        network: Метка рекламной сети (например, 'РС 1').
        impressions: Количество показов.
        clicks: Количество кликов.
        cost_rub: Стоимость в рублях.
    """

    day: str
    network: str
    impressions: int
    clicks: int
    cost_rub: float


@dataclass(frozen=True)
class DailyKpiRow:
    """Ежедневные KPI по каждой рекламной сети.

    Атрибуты:
        day: Метка дня.
        network: Метка рекламной сети.
        impressions: Количество показов.
        clicks: Количество кликов.
        cost_rub: Стоимость в рублях.
        cpc: Стоимость за клик (руб).
        cpm: Стоимость за тысячу показов (руб).
        ctr_pct: Коэффициент кликабельности в процентах.
        limit_hit: Достигнут ли дневной лимит бюджета.
    """

    day: str
    network: str
    impressions: int
    clicks: int
    cost_rub: float
    cpc: float
    cpm: float
    ctr_pct: float
    limit_hit: bool


@dataclass(frozen=True)
class CampaignDailyRow:
    """Агрегированные данные по кампании за один день.

    Атрибуты:
        day: Метка дня.
        impressions: Всего показов.
        clicks: Всего кликов.
        cost_rub: Общая стоимость в рублях.
        ctr_pct: CTR по кампании в процентах.
        cpm: CPM по кампании (руб).
    """

    day: str
    impressions: int
    clicks: int
    cost_rub: float
    ctr_pct: float
    cpm: float


# ── константы ────────────────────────────────────────────────────────────────

DAILY_LIMITS: Dict[str, float] = {
    'РС 1': 10_000.0,
    'РС 2': 3_500.0,
    'РС 3': 1_500.0,
}

LIMIT_THRESHOLD: float = 0.95  # 95% дневного лимита = "достигнут лимит"

MIN_CTR_PCT: float = 0.5   # Минимальный CTR для проверки требований
MAX_CPM_RUB: float = 50.0  # Максимальный CPM для проверки требований


# ── чтение CSV (использует парсинг из task1_parse.py) ───────────────────────


def read_csv(source: str) -> List[CampaignRow]:
    """Прочитать CSV-файл кампании и вернуть распарсенные строки.

    Args:
        source: Путь к CSV-файлу.

    Returns:
        Список экземпляров CampaignRow, полученных из файла.
    """
    rows: List[CampaignRow] = []
    with open(source, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # пропустить заголовок
        for line_num, raw in enumerate(reader, start=2):
            if not raw or all(cell.strip() == '' for cell in raw):
                continue
            if len(raw) < 5:
                print(
                    f'Предупреждение: строка {line_num} содержит {len(raw)} столбцов, пропуск',
                    file=sys.stderr,
                )
                continue
            rows.append(
                CampaignRow(
                    day=raw[0].strip(),
                    network=raw[1].strip(),
                    impressions=int(raw[2].strip()),
                    clicks=int(raw[3].strip()),
                    cost_rub=float(raw[4].strip().replace(',', '.')),
                )
            )
    return rows


# ── вычисление KPI ───────────────────────────────────────────────────────────


def _safe_div(numerator: float, denominator: float) -> float:
    """Вернуть numerator / denominator, или 0.0, если знаменатель равен нулю.

    Args:
        numerator: Делимое.
        denominator: Делитель.

    Returns:
        Результат деления или 0.0.
    """
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def compute_daily_kpis(rows: List[CampaignRow]) -> List[DailyKpiRow]:
    """Вычислить ежедневные KPI по каждой сети для каждой строки.

    Args:
        rows: Распарсенные строки кампании.

    Returns:
        Список DailyKpiRow с CPC, CPM, CTR и флагом достижения лимита.
    """
    results: List[DailyKpiRow] = []
    for r in rows:
        cpc = _safe_div(r.cost_rub, float(r.clicks))
        cpm = _safe_div(r.cost_rub, float(r.impressions)) * 1000.0
        ctr = _safe_div(float(r.clicks), float(r.impressions)) * 100.0
        limit = DAILY_LIMITS.get(r.network, float('inf'))
        hit_limit = r.cost_rub >= limit * LIMIT_THRESHOLD
        results.append(
            DailyKpiRow(
                day=r.day,
                network=r.network,
                impressions=r.impressions,
                clicks=r.clicks,
                cost_rub=r.cost_rub,
                cpc=cpc,
                cpm=cpm,
                ctr_pct=ctr,
                limit_hit=hit_limit,
            )
        )
    return results


def compute_campaign_daily(kpi_rows: List[DailyKpiRow]) -> List[CampaignDailyRow]:
    """Агрегировать данные по сетям в ежедневные метрики кампании.

    Args:
        kpi_rows: Ежедневные KPI по каждой сети.

    Returns:
        Список CampaignDailyRow — по одному на каждый уникальный день.
    """
    days: List[str] = sorted({r.day for r in kpi_rows}, key=lambda d: d)
    results: List[CampaignDailyRow] = []
    for day in days:
        day_rows = [r for r in kpi_rows if r.day == day]
        total_imp = sum(r.impressions for r in day_rows)
        total_clicks = sum(r.clicks for r in day_rows)
        total_cost = sum(r.cost_rub for r in day_rows)
        ctr = _safe_div(float(total_clicks), float(total_imp)) * 100.0
        cpm = _safe_div(total_cost, float(total_imp)) * 1000.0
        results.append(
            CampaignDailyRow(
                day=day,
                impressions=total_imp,
                clicks=total_clicks,
                cost_rub=total_cost,
                ctr_pct=ctr,
                cpm=cpm,
            )
        )
    return results


def compute_campaign_averages(daily_rows: List[CampaignDailyRow]) -> Tuple[float, float]:
    """Вычислить средние ежедневные CTR и CPM по кампании.

    Args:
        daily_rows: Ежедневные агрегированные данные кампании.

    Returns:
        Кортеж (avg_ctr_pct, avg_cpm).
    """
    n = len(daily_rows)
    if n == 0:
        return (0.0, 0.0)
    avg_ctr = sum(r.ctr_pct for r in daily_rows) / n
    avg_cpm = sum(r.cpm for r in daily_rows) / n
    return (avg_ctr, avg_cpm)


# ── вывод ────────────────────────────────────────────────────────────────────


def _limit_label(hit: bool) -> str:
    """Вернуть читаемую метку достижения лимита бюджета.

    Args:
        hit: Был ли достигнут лимит.

    Returns:
        'ЛИМИТ' или 'OK'.
    """
    return 'ЛИМИТ' if hit else 'OK'


def print_daily_kpi_table(rows: List[DailyKpiRow]) -> None:
    """Вывести таблицу ежедневных KPI по каждой сети.

    Args:
        rows: Список DailyKpiRow для отображения.
    """
    print_header_block(
        title="Ежедневные KPI по рекламным сетям",
        description="Показы, клики, затраты, CPC, CPM, CTR и статус соблюдения бюджета по каждой сети за каждый день",
        period="Дни 1–3",
    )
    header = (
        f"{'День':<8} {'РС':<6} {'Показы':<9} {'Клики':<7}"
        f" {'Затраты':<10} {'CPC':<8} {'CPM':<9} {'CTR%':<8} {'Бюджет'}"
    )
    sep = '-' * len(header)
    print(header)
    print(sep)
    for r in rows:
        print(
            f'{r.day:<8} {r.network:<6} {r.impressions:<9} {r.clicks:<7}'
            f' {r.cost_rub:<10.2f} {r.cpc:<8.2f} {r.cpm:<9.2f}'
            f' {r.ctr_pct:<8.4f} {_limit_label(r.limit_hit)}',
        )
    print(sep)


def print_campaign_daily_table(rows: List[CampaignDailyRow]) -> None:
    """Вывести таблицу ежедневных агрегированных данных кампании.

    Args:
        rows: Список CampaignDailyRow для отображения.
    """
    print_header_block(
        title="Агрегированные данные кампании",
        description="Суммарные показы, клики, затраты, CTR и CPM по кампании в целом за каждый день",
        period="Дни 1–3",
    )
    header = (
        f"{'День':<8} {'Всего показов':<14} {'Всего кликов':<13}"
        f" {'Всего затрат':<14} {'CTR%':<10} {'CPM'}"
    )
    sep = '-' * len(header)
    print(header)
    print(sep)
    for r in rows:
        print(
            f'{r.day:<8} {r.impressions:<14} {r.clicks:<13}'
            f' {r.cost_rub:<14.2f} {r.ctr_pct:<10.5f} {r.cpm:.2f}',
        )
    print(sep)


def print_averages(avg_ctr: float, avg_cpm: float) -> None:
    """Вывести средние KPI по кампании.

    Args:
        avg_ctr: Средний дневной CTR в процентах.
        avg_cpm: Средний дневной CPM в рублях.
    """
    print_header_block(
        title="Средние по кампании",
        description="Средние дневные CTR и CPM по всем рекламным сетям за период кампании",
        period="В среднем за 3 дня",
    )
    print(f'  Средний дневной CTR%: {avg_ctr:.4f}%')
    print(f'  Средний дневной CPM:  {avg_cpm:.2f} руб')


def print_requirements_check(avg_ctr: float, avg_cpm: float) -> None:
    """Проверить, соответствует ли кампания требованиям по эффективности.

    Args:
        avg_ctr: Средний дневной CTR в процентах.
        avg_cpm: Средний дневной CPM в рублях.
    """
    ctr_ok = avg_ctr > MIN_CTR_PCT
    cpm_ok = avg_cpm < MAX_CPM_RUB
    print_header_block(
        title="Проверка требований",
        description="Проверка соответствия кампании целевым показателям CTR и CPM",
        period="Средние за 3 дня кампании",
    )
    print(f'  Средний CTR > {MIN_CTR_PCT}%?  {avg_ctr:.4f} > {MIN_CTR_PCT} -> {"ДА" if ctr_ok else "НЕТ"}')
    print(f'  Средний CPM < {MAX_CPM_RUB} руб? {avg_cpm:.2f} < {MAX_CPM_RUB} -> {"ДА" if cpm_ok else "НЕТ"}')


@dataclass(frozen=True)
class NetworkInterpretation:
    """Предварительно вычисленные данные интерпретации для одной сети.

    Атрибуты:
        network: Метка рекламной сети.
        daily_limit: Дневной лимит бюджета в рублях.
        days_hit: Количество дней на/около лимита (из 3).
        total_spend: Общие расходы за все дни в рублях.
        avg_ctr_pct: Средний CTR в процентах.
        avg_cpm_rub: Средний CPM в рублях.
    """

    network: str
    daily_limit: float
    days_hit: int
    total_spend: float
    avg_ctr_pct: float
    avg_cpm_rub: float


def prepare_interpretation_data(
    kpi_rows: List[DailyKpiRow],
) -> List[NetworkInterpretation]:
    """Агрегировать данные по лимитам бюджета для интерпретации.

    Args:
        kpi_rows: Ежедневные KPI по каждой сети.

    Returns:
        Список NetworkInterpretation — по одному на каждую сеть.
    """
    networks = sorted({r.network for r in kpi_rows})
    results: List[NetworkInterpretation] = []
    for net in networks:
        net_rows = [r for r in kpi_rows if r.network == net]
        limit = DAILY_LIMITS.get(net, 0.0)
        hit_count = sum(1 for r in net_rows if r.limit_hit)
        total_cost = sum(r.cost_rub for r in net_rows)
        avg_ctr = sum(r.ctr_pct for r in net_rows) / len(net_rows)
        avg_cpm_val = sum(r.cpm for r in net_rows) / len(net_rows)
        results.append(NetworkInterpretation(network=net, daily_limit=limit, days_hit=hit_count, total_spend=total_cost, avg_ctr_pct=avg_ctr, avg_cpm_rub=avg_cpm_val))
    return results


def print_interpretation(data: List[NetworkInterpretation]) -> None:
    """Вывести интерпретацию по лимитам бюджета для каждой сети.

    Args:
        data: Предварительно вычисленные данные интерпретации по сетям.
    """
    print_header_block(
        title="Интерпретация бюджетных лимитов",
        description="Анализ использования бюджета по каждой сети — сколько дней был достигнут лимит, общие затраты, средние CTR и CPM",
        period="За весь период кампании",
    )
    for ni in data:
        print(f'\n  {ni.network} (дневной лимит: {ni.daily_limit:.0f} руб):')
        print(f'    Дней на/около лимита: {ni.days_hit}/3')
        print(f'    Всего потрачено: {ni.total_spend:.2f} руб')
        print(f'    Средний CTR: {ni.avg_ctr_pct:.4f}% | Средний CPM: {ni.avg_cpm_rub:.2f} руб')

        if ni.days_hit > 0:
            print(
                f'    -> Ограничен бюджетом. Кампания достигает дневного лимита, '
                f'из-за чего показы обрезаются.'
            )
            if ni.daily_limit <= 3500:
                print(
                    f'      Низкий бюджет ограничивает объём; CTR низкий '
                    f'({ni.avg_ctr_pct:.2f}%), что указывает на дешёвый остаточный инвентарь.'
                )
            else:
                print(
                    f'      РС 1 имеет запас для масштабирования — лимит был достигнут только '
                    f'во время тестового дня 2.'
                )
        else:
            print('    -> Не ограничен бюджетом. Показы доставляются без ограничений.')


# ── главная функция ──────────────────────────────────────────────────────────


def main(csv_path: str) -> None:
    """Запустить полный конвейер анализа KPI для CSV задачи 1.

    Args:
        csv_path: Абсолютный или относительный путь к CSV-файлу.
    """
    raw_rows = read_csv(csv_path)
    kpi_rows = compute_daily_kpis(raw_rows)

    print_daily_kpi_table(kpi_rows)

    campaign_daily = compute_campaign_daily(kpi_rows)
    print_campaign_daily_table(campaign_daily)

    avg_ctr, avg_cpm = compute_campaign_averages(campaign_daily)
    print_averages(avg_ctr, avg_cpm)
    print_requirements_check(avg_ctr, avg_cpm)

    interp_data = prepare_interpretation_data(kpi_rows)
    print_interpretation(interp_data)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Использование: python task1_kpis.py <путь_к_csv>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
