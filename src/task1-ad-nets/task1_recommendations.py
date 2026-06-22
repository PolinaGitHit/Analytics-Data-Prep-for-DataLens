"""Скрипт рекомендаций на День 4 для рекламной кампании (Задача 1).

Читает CSV-файл кампании (3 дня x 3 сети), вычисляет KPI,
анализирует использование дневных лимитов бюджета, даёт конкретные
рекомендации на День 4, проецирует результаты Дня 4 и проверяет требования.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from print_utils import print_header_block
from typing import Any, Dict, List, Tuple

from task1_kpis import (
    DAILY_LIMITS,
    LIMIT_THRESHOLD,
    MIN_CTR_PCT,
    MAX_CPM_RUB,
    CampaignDailyRow,
    CampaignRow,
    DailyKpiRow,
    read_csv,
    compute_daily_kpis,
    compute_campaign_daily,
    compute_campaign_averages,
)


# ── константы ─────────────────────────────────────────────────────────────────

CPC_BASELINE: float = 6.0

# Рекомендуемые параметры Дня 4 для каждой сети
Day4Params = Dict[str, Dict[str, float]]

DAY4_PARAMS: Day4Params = {
    # РС 1: поднять CPC обратно до уровня теста ставки (7 руб), поднять лимит,
    #        чтобы обеспечить показы на весь день.
    'РС 1': {
        'cpc': 7.0,
        'daily_limit': 12_000.0,
    },
    # РС 2: оставить CPC на базовом уровне, лимит не менять — низкий CTR
    #        тянет средний по кампании вниз.
    'РС 2': {
        'cpc': CPC_BASELINE,
        'daily_limit': 3_500.0,
    },
    # РС 3: оставить CPC на базовом уровне, лимит не менять — очень низкий CTR.
    'РС 3': {
        'cpc': CPC_BASELINE,
        'daily_limit': 1_500.0,
    },
}


# ── типы для анализа ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BudgetUtilization:
    """Сводка использования бюджета для одной сети за 3 дня.

    Атрибуты:
        network: Название сети.
        daily_limit: Дневной лимит бюджета (руб).
        days_hit: Количество дней у лимита (из 3).
        total_impressions: Всего показов за 3 дня.
        total_cost: Всего затрат за 3 дня (руб).
        potential_impressions: Оценка показов без ограничения бюджета.
        lost_impressions: Потенциальные минус фактические показы.
    """

    network: str
    daily_limit: float
    days_hit: int
    total_impressions: int
    total_cost: float
    potential_impressions: int
    lost_impressions: int


@dataclass(frozen=True)
class NetworkRecommendation:
    """Рекомендация на День 4 для одной сети.

    Атрибуты:
        network: Название сети.
        cpc_action: Описание действия по ставке CPC.
        limit_action: Описание действия по дневному лимиту.
        rationale: Краткое обоснование.
    """

    network: str
    cpc_action: str
    limit_action: str
    rationale: str


@dataclass(frozen=True)
class Day4Projection:
    """Прогноз результатов Дня 4 для одной сети.

    Атрибуты:
        network: Название сети.
        impressions: Прогноз показов.
        clicks: Прогноз кликов.
        cost_rub: Прогноз затрат (руб).
        ctr_pct: Прогноз CTR (%).
        cpm_rub: Прогноз CPM (руб).
    """

    network: str
    impressions: int
    clicks: int
    cost_rub: float
    ctr_pct: float
    cpm_rub: float


# ── анализ ────────────────────────────────────────────────────────────────────


def _safe_div(numerator: float, denominator: float) -> float:
    """Вернуть numerator / denominator, или 0.0 если denominator равен нулю."""
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _analyse_network_utilization(
    kpi_rows: List[DailyKpiRow],
    network: str,
) -> BudgetUtilization:
    """Проанализировать использование бюджета для одной сети."""
    net_rows = [r for r in kpi_rows if r.network == network]
    limit = DAILY_LIMITS.get(network, 0.0)
    hit_count = sum(1 for r in net_rows if r.limit_hit)
    total_imp = sum(r.impressions for r in net_rows)
    total_cost = sum(r.cost_rub for r in net_rows)

    # Оценка показов при отсутствии бюджетных ограничений.
    potential = 0
    for r in net_rows:
        if r.limit_hit and r.cpm > 0.0:
            day_potential = int(limit / (r.cpm / 1000.0))
            potential += max(day_potential, r.impressions)
        else:
            potential += r.impressions

    lost = potential - total_imp
    return BudgetUtilization(
        network=network,
        daily_limit=limit,
        days_hit=hit_count,
        total_impressions=total_imp,
        total_cost=total_cost,
        potential_impressions=potential,
        lost_impressions=lost,
    )


def analyse_budget_utilization(
    kpi_rows: List[DailyKpiRow],
) -> List[BudgetUtilization]:
    """Проанализировать, как каждая сеть использовала свой дневной лимит.

    Вычисляет потенциальные показы в предположении отсутствия лимита: для
    дней, когда лимит был достигнут, экстраполирует показы на основе CPM
    дня без лимита. Для дней БЕЗ достижения лимита фактические показы уже
    считаются «потенциальными».

    Args:
        kpi_rows: Строки дневных KPI по сетям.

    Returns:
        Список BudgetUtilization, по одному на сеть.
    """
    networks = sorted({r.network for r in kpi_rows})
    return [_analyse_network_utilization(kpi_rows, net) for net in networks]


def _recommend_rs1(
    avg_ctr: float, hit_count: int,
) -> NetworkRecommendation:
    """Рекомендация на День 4 для РС 1 (лучший CTR)."""
    return NetworkRecommendation(
        network='РС 1',
        cpc_action='Поднять CPC до 7.0 руб (уровень теста ставки)',
        limit_action='Поднять дневной лимит до 12 000 руб',
        rationale=(
            f'Лучший CTR ({avg_ctr:.2f}%) тянет средний кампании вверх. '
            f'Всего {hit_count}/3 дня у лимита. Повышение CPC даёт более '
            f'агрессивную борьбу за показы, больший лимит предотвращает '
            f'раннюю остановку.'
        ),
    )


def _recommend_rs2(
    avg_ctr: float, hit_count: int,
) -> NetworkRecommendation:
    """Рекомендация на День 4 для РС 2 (низкий CTR)."""
    return NetworkRecommendation(
        network='РС 2',
        cpc_action='Оставить CPC на уровне 6.0 руб',
        limit_action='Оставить дневной лимит на уровне 3 500 руб',
        rationale=(
            f'CTR ({avg_ctr:.2f}%) ниже порога 0.5%% — увеличение объёмов '
            f'рискует опустить средний CTR кампании ниже требования. '
            f'Лимит уже выбран ежедневно ({hit_count}/3 дня).'
        ),
    )


def _recommend_rs3(
    avg_ctr: float, avg_cpm_val: float,
) -> NetworkRecommendation:
    """Рекомендация на День 4 для РС 3 (очень низкий CTR)."""
    return NetworkRecommendation(
        network='РС 3',
        cpc_action='Оставить CPC на уровне 6.0 руб',
        limit_action='Оставить дневной лимит на уровне 1 500 руб',
        rationale=(
            f'Очень низкий CTR ({avg_ctr:.2f}%) — увеличение объёмов '
            f'существенно разбавит кампанийный CTR. CPM самый дешёвый '
            f'({avg_cpm_val:.2f} руб), но ценность показов низкая.'
        ),
    )


def _else_recommendation(net: str) -> NetworkRecommendation:
    """Запасная рекомендация для неизвестных сетей."""
    return NetworkRecommendation(
        network=net,
        cpc_action='Проверить данные',
        limit_action='Проверить данные',
        rationale='Неизвестная сеть — рекомендация отсутствует.',
    )


def build_recommendations(kpi_rows: List[DailyKpiRow]) -> List[NetworkRecommendation]:
    """Сформировать рекомендации на День 4 для каждой сети на основе анализа KPI."""
    networks = sorted({r.network for r in kpi_rows})
    results: List[NetworkRecommendation] = []
    for net in networks:
        net_rows = [r for r in kpi_rows if r.network == net]
        avg_ctr = sum(r.ctr_pct for r in net_rows) / len(net_rows)
        avg_cpm_val = sum(r.cpm for r in net_rows) / len(net_rows)
        hit_count = sum(1 for r in net_rows if r.limit_hit)
        if net == 'РС 1':
            rec = _recommend_rs1(avg_ctr, hit_count)
        elif net == 'РС 2':
            rec = _recommend_rs2(avg_ctr, hit_count)
        elif net == 'РС 3':
            rec = _recommend_rs3(avg_ctr, avg_cpm_val)
        else:
            rec = _else_recommendation(net)
        results.append(rec)
    return results


def _project_rs1(net_rows: List[DailyKpiRow], net: str, params: Dict[str, float]) -> Tuple[int, float, int]:
    """Спрогнозировать День 4 для РС 1, используя День 2 (CPC=7) как аналог."""
    day2 = [r for r in net_rows if r.day == 'День 2']
    ref = day2[0] if day2 else net_rows[-1]
    scale = params.get('daily_limit', 10_000.0) / DAILY_LIMITS.get(net, 10_000.0)
    projected_imp = int(ref.impressions * scale)
    projected_cost = min(
        params.get('daily_limit', 10_000.0),
        projected_imp * ref.cpm / 1000.0,
    )
    projected_clicks = int(_safe_div(projected_cost, params.get('cpc', 6.0)))
    return projected_imp, projected_cost, projected_clicks


def _project_other(net_rows: List[DailyKpiRow], net: str, params: Dict[str, float]) -> Tuple[int, float, int]:
    """Спрогнозировать День 4 для сетей с неизменными параметрами."""
    avg_imp = int(sum(r.impressions for r in net_rows) / len(net_rows))
    avg_cost = sum(r.cost_rub for r in net_rows) / len(net_rows)
    avg_clicks = int(sum(r.clicks for r in net_rows) / len(net_rows))
    limit = params.get('daily_limit', DAILY_LIMITS.get(net, 0.0))
    projected_cost = min(limit, avg_cost)
    ratio = projected_cost / avg_cost if avg_cost > 0 else 1.0
    projected_imp = int(avg_imp * ratio)
    projected_clicks = int(avg_clicks * ratio)
    return projected_imp, projected_cost, projected_clicks


def _project_day4_for_network(
    net_rows: List[DailyKpiRow],
    net: str,
    params: Dict[str, float],
) -> Day4Projection:
    """Спрогнозировать результаты Дня 4 для одной сети."""
    if net == 'РС 1':
        projected_imp, projected_cost, projected_clicks = _project_rs1(net_rows, net, params)
    else:
        projected_imp, projected_cost, projected_clicks = _project_other(net_rows, net, params)
    ctr = _safe_div(float(projected_clicks), float(projected_imp)) * 100.0
    cpm = _safe_div(projected_cost, float(projected_imp)) * 1000.0
    return Day4Projection(
        network=net, impressions=projected_imp, clicks=projected_clicks,
        cost_rub=projected_cost, ctr_pct=ctr, cpm_rub=cpm,
    )


def _compute_campaign_totals(projections: List[Day4Projection]) -> Dict[str, float]:
    """Вычислить общекампанийные агрегаты Дня 4 на основе проекций по сетям."""
    total_imp = sum(p.impressions for p in projections)
    total_clicks = sum(p.clicks for p in projections)
    total_cost = sum(p.cost_rub for p in projections)
    day4_ctr = _safe_div(float(total_clicks), float(total_imp)) * 100.0
    day4_cpm = _safe_div(total_cost, float(total_imp)) * 1000.0
    return {
        'impressions': float(total_imp),
        'clicks': float(total_clicks),
        'cost_rub': total_cost,
        'ctr_pct': day4_ctr,
        'cpm_rub': day4_cpm,
    }


def project_day4(
    kpi_rows: List[DailyKpiRow],
    day4_params: Day4Params,
) -> Tuple[List[Day4Projection], Dict[str, float]]:
    """Спрогнозировать результаты Дня 4 для каждой сети по рекомендованным параметрам."""
    networks = sorted({r.network for r in kpi_rows})
    projections: List[Day4Projection] = [
        _project_day4_for_network(
            [r for r in kpi_rows if r.network == net], net,
            day4_params.get(net, {}),
        )
        for net in networks
    ]
    return projections, _compute_campaign_totals(projections)


def verify_day4(
    existing_daily: List[CampaignDailyRow],
    day4_campaign: Dict[str, float],
) -> Dict[str, Any]:
    """Проверить, что прогноз Дня 4 удерживает общекампанийные требования."""
    existing_avg_ctr, existing_avg_cpm = compute_campaign_averages(existing_daily)

    # Вычислить новые средние по кампании с учётом Дня 4.
    all_days_ctr = existing_avg_ctr * len(existing_daily) + day4_campaign['ctr_pct']
    all_days_cpm = existing_avg_cpm * len(existing_daily) + day4_campaign['cpm_rub']
    new_count = len(existing_daily) + 1
    new_avg_ctr = all_days_ctr / new_count
    new_avg_cpm = all_days_cpm / new_count

    ctr_ok = new_avg_ctr > MIN_CTR_PCT
    cpm_ok = new_avg_cpm < MAX_CPM_RUB

    return {
        'new_avg_ctr': new_avg_ctr,
        'new_avg_cpm': new_avg_cpm,
        'ctr_ok': ctr_ok,
        'cpm_ok': cpm_ok,
        'overall_ok': ctr_ok and cpm_ok,
    }


# ── вывод ─────────────────────────────────────────────────────────────────────


def print_current_status(kpi_rows: List[DailyKpiRow]) -> None:
    """Вывести сводку текущего состояния по каждой сети.

    Args:
        kpi_rows: Строки дневных KPI по сетям.
    """
    networks = sorted({r.network for r in kpi_rows})
    print_header_block(
        title="Текущее состояние рекламных сетей",
        description="Средний CTR, CPM, суммарные показы, затраты и количество дней у лимита бюджета по каждой сети",
        period="Дни 1–3 (итоги на текущий момент)",
    )

    header = (
        f"{'РС':<8} {'Ср. CTR%':<12} {'Ср. CPM':<12}"
        f" {'Всего показов':<16} {'Всего затрат':<14} {'Дней у лимита':<14}"
    )
    print(header)
    print('-' * len(header))

    for net in networks:
        net_rows = [r for r in kpi_rows if r.network == net]
        avg_ctr = sum(r.ctr_pct for r in net_rows) / len(net_rows)
        avg_cpm_val = sum(r.cpm for r in net_rows) / len(net_rows)
        total_imp = sum(r.impressions for r in net_rows)
        total_cost = sum(r.cost_rub for r in net_rows)
        hit_count = sum(1 for r in net_rows if r.limit_hit)
        print(
            f'{net:<8} {avg_ctr:<12.4f} {avg_cpm_val:<12.2f}'
            f' {total_imp:<16} {total_cost:<14.2f} {hit_count}/3'
        )


def print_budget_utilization(data: List[BudgetUtilization]) -> None:
    """Вывести анализ использования бюджета.

    Args:
        data: Список BudgetUtilization.
    """
    print_header_block(
        title="Анализ использования бюджета",
        description="Лимит показов в день, количество дней достижения лимита, фактические vs потенциальные показы, потерянный охват",
        period="Дни 1–3",
    )

    header = (
        f"{'РС':<8} {'Лимит':<10} {'Дней HIT':<12}"
        f" {'Факт. показы':<14} {'Потенц. показы':<16} {'Потеряно':<10}"
    )
    print(header)
    print('-' * len(header))

    for d in data:
        print(
            f'{d.network:<8} {d.daily_limit:<10.0f} {d.days_hit}/3'
            f'           {d.total_impressions:<14} {d.potential_impressions:<16}'
            f' {d.lost_impressions:<10}'
        )


def print_recommendations(recs: List[NetworkRecommendation]) -> None:
    """Вывести таблицу рекомендаций на День 4.

    Args:
        recs: Список NetworkRecommendation.
    """
    print('\n' + '=' * 72)
    print('  РЕКОМЕНДАЦИИ НА ДЕНЬ 4')
    print('=' * 72)

    for rec in recs:
        print(f'\n  --- {rec.network} ---')
        print(f'  CPC:          {rec.cpc_action}')
        print(f'  Лимит:        {rec.limit_action}')
        print(f'  Обоснование:  {rec.rationale}')


def _print_day4_header() -> str:
    """Вывести заголовок для прогноза Дня 4; вернуть разделитель."""
    print_header_block(
        title="Прогноз результатов дня 4",
        description="Прогнозируемые показы, клики, затраты, CTR и CPM по каждой сети при рекомендованных параметрах",
        period="День 4 (прогноз)",
    )
    header = (
        f"{'РС':<8} {'Показы':<12} {'Клики':<10}"
        f" {'Затраты':<12} {'CTR%':<10} {'CPM':<10}"
    )
    print(header)
    sep = '-' * len(header)
    print(sep)
    return sep


def print_day4_projections(
    projections: List[Day4Projection],
    campaign: Dict[str, float],
) -> None:
    """Вывести прогнозируемые результаты Дня 4.

    Args:
        projections: Список Day4Projection по сетям.
        campaign: Словарь с общекампанийными итогами Дня 4.
    """
    sep = _print_day4_header()

    for p in projections:
        print(
            f'{p.network:<8} {p.impressions:<12} {p.clicks:<10}'
            f' {p.cost_rub:<12.2f} {p.ctr_pct:<10.4f} {p.cpm_rub:<10.2f}'
        )

    print(sep)
    print(
        f'{"Всего":<8} {int(campaign["impressions"]):<12} {int(campaign["clicks"]):<10}'
        f' {campaign["cost_rub"]:<12.2f} {campaign["ctr_pct"]:<10.4f} {campaign["cpm_rub"]:<10.2f}'
    )


def _print_verification_result(result: Dict[str, Any]) -> None:
    """Вывести результат прохождения/непрохождения проверок требований."""
    ctr_label = 'ДА' if result['ctr_ok'] else 'НЕТ'
    cpm_label = 'ДА' if result['cpm_ok'] else 'НЕТ'
    overall_label = 'ПРОЙДЕН' if result['overall_ok'] else 'НЕ ПРОЙДЕН'
    print(
        f'  CTR > {MIN_CTR_PCT}%?  {result["new_avg_ctr"]:.4f} > {MIN_CTR_PCT}'
        f'  -> {ctr_label}'
    )
    print(
        f'  CPM < {MAX_CPM_RUB} руб? {result["new_avg_cpm"]:.2f} < {MAX_CPM_RUB}'
        f'  -> {cpm_label}'
    )
    print(
        f'  ИТОГО: {overall_label} --'
        f' {"требования выполнены" if result["overall_ok"] else "требования не выполнены"}'
    )


def print_verification(
    existing_daily: List[CampaignDailyRow],
    result: Dict[str, Any],
) -> None:
    """Вывести проверку требований после добавления Дня 4.

    Args:
        existing_daily: CampaignDailyRow для Дней 1–3.
        result: Словарь с результатами проверки.
    """
    existing_avg_ctr, existing_avg_cpm = compute_campaign_averages(existing_daily)

    print_header_block(
        title="Верификация рекомендаций",
        description="Проверка соблюдения требований по CTR и CPM после добавления прогноза Дня 4",
        period="Дни 1–4 (включая прогноз)",
    )
    print(
        f'  Дни 1–3 ср. CTR: {existing_avg_ctr:.4f}%'
        f'  |  +День 4: {result["new_avg_ctr"]:.4f}%'
    )
    print(
        f'  Дни 1–3 ср. CPM: {existing_avg_cpm:.2f} руб'
        f'  |  +День 4: {result["new_avg_cpm"]:.2f} руб'
    )
    print()
    _print_verification_result(result)


def _print_summary_strategy() -> None:
    """Вывести маркированный список стратегии Дня 4."""
    print('  Цель кампании — МАКСИМУМ ПОКАЗОВ при сохранении')
    print(f'  среднего CTR кампании > {MIN_CTR_PCT}% и CPM < {MAX_CPM_RUB} руб.\n')
    print('  Стратегия на День 4:')
    print(
        '  1. Поднять CPC РС 1 до 7 руб (с 6 руб) и дневной лимит до'
        '\n     12 000 руб — захватить больше высоко-CTR-показов. У РС 1'
        '\n     единственный CTR выше 0.5% (в среднем 1.33%).\n'
    )
    print(
        '  2. Оставить РС 2 на CPC=6 руб и лимите=3 500 руб — её низкий CTR'
        '\n     (0.45%) разбавит средний кампании при масштабировании.\n'
    )
    print(
        '  3. Оставить РС 3 на CPC=6 руб и лимите=1 500 руб — очень низкий'
        '\n     CTR (0.16%) делает масштабирование рискованным для требования по CTR.\n'
    )


def _print_summary_totals(projections: List[Day4Projection]) -> None:
    """Вывести прогнозируемые агрегаты Дня 4."""
    total_imp = sum(p.impressions for p in projections)
    total_cost = sum(p.cost_rub for p in projections)
    print(
        f'  Прогноз Дня 4: {total_imp:,} показов'
        f' при затратах {total_cost:.2f} руб.'
    )
    print()


def print_summary(projections: List[Day4Projection]) -> None:
    """Вывести краткую сводку ключевых рекомендаций.

    Args:
        projections: Список Day4Projection.
    """
    print('\n' + '=' * 72)
    print('  СВОДКА КЛЮЧЕВЫХ РЕКОМЕНДАЦИЙ')
    print('=' * 72)
    print()
    _print_summary_strategy()
    _print_summary_totals(projections)


# ── main ──────────────────────────────────────────────────────────────────────


def _run_pipeline(csv_path: str) -> None:
    """Запустить полный конвейер рекомендаций."""
    raw_rows: List[CampaignRow] = read_csv(csv_path)
    kpi_rows: List[DailyKpiRow] = compute_daily_kpis(raw_rows)
    print_current_status(kpi_rows)
    budget_data = analyse_budget_utilization(kpi_rows)
    print_budget_utilization(budget_data)
    recs = build_recommendations(kpi_rows)
    print_recommendations(recs)
    projections, campaign_totals = project_day4(kpi_rows, DAY4_PARAMS)
    print_day4_projections(projections, campaign_totals)
    existing_daily = compute_campaign_daily(kpi_rows)
    verify_result = verify_day4(existing_daily, campaign_totals)
    print_verification(existing_daily, verify_result)
    print_summary(projections)


def main(csv_path: str) -> None:
    """Точка входа с разбором аргументов."""
    _run_pipeline(csv_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(
            'Использование: python task1_recommendations.py <путь_к_csv>',
            file=sys.stderr,
        )
        sys.exit(1)
    main(sys.argv[1])
