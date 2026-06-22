"""Парсинг и валидация CSV-данных Задачи 1 — анализ KPI рекламных сетей.

Читает CSV-файл кампании 3 дня × 3 сети, нормализует столбцы, вычисляет CPC,
выводит отформатированную таблицу и проверяет, что CPC ≈ 6 руб для всех строк.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from print_utils import print_header_block


@dataclass(frozen=True)
class CampaignRow:
    """Одна строка данных кампании после парсинга и вычисления CPC.

    Атрибуты:
        day: Метка дня (например 'День 1').
        network: Метка сети (например 'РС 1').
        impressions: Количество показов рекламы.
        clicks: Количество кликов по рекламе.
        cost_rub: Стоимость в рублях.
        cpc: Цена за клик в рублях или None, если ещё не вычислена.
    """

    day: str
    network: str
    impressions: int
    clicks: int
    cost_rub: float
    cpc: Optional[float] = None


EXPECTED_COLUMNS: int = 5


def _parse_line(raw: List[str], line_num: int) -> CampaignRow:
    """Преобразует одну строку CSV в CampaignRow.

    Аргументы:
        raw: Список строковых ячеек из строки CSV.
        line_num: Номер строки для диагностических сообщений.

    Возвращает:
        CampaignRow с нормализованными числовыми полями.

    Исключения:
        ValueError: Если в строке меньше EXPECTED_COLUMNS ячеек.
    """
    if len(raw) < EXPECTED_COLUMNS:
        raise ValueError(
            f'Строка {line_num}: ожидалось {EXPECTED_COLUMNS} столбцов, '
            f'получено {len(raw)}.'
        )
    day = raw[0].strip()
    network = raw[1].strip()
    impressions = int(raw[2].strip())
    clicks = int(raw[3].strip())
    cost_rub = float(raw[4].strip().replace(',', '.'))
    return CampaignRow(
        day=day,
        network=network,
        impressions=impressions,
        clicks=clicks,
        cost_rub=cost_rub,
    )


def read_csv(source: str) -> List[CampaignRow]:
    """Читает CSV-файл кампании и возвращает распарсенные строки.

    Аргументы:
        source: Путь к CSV-файлу.

    Возвращает:
        Список экземпляров CampaignRow, полученных из файла.
    """
    rows: List[CampaignRow] = []
    with open(source, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # пропустить заголовок: Дата,РС,Показы,Клики,"Затраты, руб"
        for line_num, raw in enumerate(reader, start=2):
            if not raw or all(cell.strip() == '' for cell in raw):
                continue
            if len(raw) < EXPECTED_COLUMNS:
                print(
                    f'Предупреждение: строка {line_num} содержит {len(raw)} столбцов, '
                    f'пропускаем',
                    file=sys.stderr,
                )
                continue
            row = _parse_line(raw, line_num)
            rows.append(row)
    return rows


class CpcCalculator:
    """Вычисляет CPC (цену за клик) из CampaignRow."""

    def compute(self, row: CampaignRow) -> float:
        """Вычисляет CPC = cost_rub / clicks.

        Аргументы:
            row: Строка кампании с затратами и кликами.

        Возвращает:
            Значение CPC или 0.0, если кликов нет.
        """
        if row.clicks == 0:
            return 0.0
        return row.cost_rub / row.clicks


def attach_cpc(
    rows: List[CampaignRow], calculator: CpcCalculator,
) -> List[CampaignRow]:
    """Возвращает новые экземпляры CampaignRow с прикреплённым CPC.

    Аргументы:
        rows: Исходные строки без CPC.
        calculator: Стратегия вычисления CPC.

    Возвращает:
        Новый список строк с заполненным CPC.
    """
    result: List[CampaignRow] = []
    for r in rows:
        result.append(
            CampaignRow(
                day=r.day,
                network=r.network,
                impressions=r.impressions,
                clicks=r.clicks,
                cost_rub=r.cost_rub,
                cpc=calculator.compute(r),
            )
        )
    return result


class TablePrinter:
    """Форматирует и выводит данные кампании в виде читаемой таблицы."""

    @staticmethod
    def print_table(rows: Sequence[CampaignRow]) -> None:
        """Выводит все строки кампании со столбцом CPC в stdout.

        Аргументы:
            rows: Строки кампании с прикреплённым CPC.
        """
        print_header_block(
            title="ПаРсИнг и CPC",
            description="Исходные данные кампании — показы, клики, затраты и CPC по каждой рекламной сети за каждый день",
            period="Дни 1–3 (период кампании)",
        )
        header = (
            f"{'День':<10} {'РС':<8} {'Показы':<10} {'Клики':<8} "
            f"{'Затраты, руб':<14} {'CPC, руб':<10}"
        )
        sep = '-' * len(header)
        print(header)
        print(sep)
        for r in rows:
            cpc_str = f'{r.cpc:.2f}' if r.cpc is not None else 'N/A'
            print(
                f'{r.day:<10} {r.network:<8} {r.impressions:<10} {r.clicks:<8} '
                f'{r.cost_rub:<14.2f} {cpc_str:<10}',
            )
        print(sep + '\n')


class CpcValidator:
    """Проверяет, что значения CPC близки к ожидаемому базовому значению 6 руб."""

    BASELINE_CPC: float = 6.0
    TOLERANCE: float = 0.15

    def validate(
        self,
        rows: Sequence[CampaignRow],
        known_deviations: Optional[Dict[Tuple[str, str], str]] = None,
    ) -> List[str]:
        """Проверяет CPC каждой строки относительно базового значения и возвращает предупреждения.

        Аргументы:
            rows: Строки кампании с прикреплённым CPC.
            known_deviations: Необязательное отображение (день, сеть) в строку
                причины. Предупреждения для совпадающих строк дополняются причиной.

        Возвращает:
            Список понятных предупреждающих строк для строк, где CPC
            отклоняется за пределы допуска.
        """
        known_deviations = known_deviations or {}
        warnings: List[str] = []
        for r in rows:
            if r.cpc is None:
                warnings.append(f'{r.day} {r.network}: CPC отсутствует')
                continue
            diff = abs(r.cpc - self.BASELINE_CPC)
            if diff > self.TOLERANCE:
                annotation = known_deviations.get((r.day, r.network))
                suffix = f' (известно — {annotation})' if annotation else ''
                warnings.append(
                    f'{r.day} {r.network}: CPC = {r.cpc:.2f} руб '
                    f'(ожидалось ~ {self.BASELINE_CPC} руб, отклонение = {diff:.2f})'
                    f'{suffix}',
                )
        return warnings


def print_summary(rows: Sequence[CampaignRow]) -> None:
    """Выводит сводную статистику по каждой сети (итоги и средний CPC).

    Аргументы:
        rows: Все строки кампании с прикреплённым CPC.
    """
    print_header_block(
        title="Сводка по рекламным сетям",
        description="Итоговые метрики за 3 дня — суммарные показы, клики, затраты и средний CPC по каждой сети",
        period="За весь период кампании (Дни 1–3)",
    )
    header = (
        f"{'РС':<8} {'Дней':<6} {'Всего показов':<14} {'Всего кликов':<12} "
        f"{'Всего затрат':<14} {'Средний CPC':<12}"
    )
    print(header)
    print('-' * 68)
    networks = sorted({r.network for r in rows})
    for net in networks:
        net_rows = [r for r in rows if r.network == net]
        total_imp = sum(r.impressions for r in net_rows)
        total_clicks = sum(r.clicks for r in net_rows)
        total_cost = sum(r.cost_rub for r in net_rows)
        avg_cpc = total_cost / total_clicks if total_clicks else 0.0
        print(
            f'{net:<8} {len(net_rows):<6} {total_imp:<14} {total_clicks:<12} '
            f'{total_cost:<14.2f} {avg_cpc:<12.2f}',
        )
    print()


def main(csv_path: str) -> None:
    """Запускает полный конвейер парсинга и валидации для CSV Задачи 1.

    Аргументы:
        csv_path: Абсолютный или относительный путь к CSV-файлу.
    """
    calculator = CpcCalculator()
    printer = TablePrinter()
    validator = CpcValidator()

    rows = read_csv(csv_path)
    rows = attach_cpc(rows, calculator)

    printer.print_table(rows)

    known_deviations: Dict[Tuple[str, str], str] = {
        ('День 2', 'РС 1'): 'тест ставки',
    }
    warnings = validator.validate(rows, known_deviations=known_deviations)
    if warnings:
        print('Отклонения CPC (ожидалось ~6 руб):')
        for w in warnings:
            print(f'  * {w}')
        print()
    else:
        print('OK: CPC = 6 руб для всех строк.')
        print()

    print_summary(rows)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Использование: python task1_parse.py <csv_path>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])