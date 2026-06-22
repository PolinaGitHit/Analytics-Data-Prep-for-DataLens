"""Общие утилиты для форматированного вывода таблиц."""


# ── print_header_block ───────────────────────────────────────────────────────


def print_header_block(title: str, description: str, period: str) -> None:
    """Напечатать заголовок-раздел перед таблицей.

    Args:
        title: Название раздела. Выводится ЗАГЛАВНЫМИ.
        description: Описание метрик таблицы. Sentence case.
        period: Период или разрез данных. Sentence case.
    """
    title_text = title.upper()
    description_text = description[0].upper() + description[1:].lower() if description else ""
    period_text = period[0].upper() + period[1:].lower() if period else ""

    sep = "=" * max(len(title_text) + 4, 40)
    print(f"\n{sep}")
    print(f"  {title_text}")
    print(f"  {description_text}")
    print(f"  {period_text}")
    print(sep)
    print()