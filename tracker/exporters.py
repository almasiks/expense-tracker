"""Export strategies: one class per output format.

Each exporter writes a list of expenses to a file. ExpenseService.export()
picks the strategy from EXPORTERS by format name.
"""

import json
from collections.abc import Sequence
from typing import Protocol

from tracker.models import Expense


class Exporter(Protocol):
    def export(self, expenses: Sequence[Expense], path: str) -> None: ...


class CsvExporter:
    def export(self, expenses: Sequence[Expense], path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("id,date,category,amount,description\n")
            f.writelines(
                f"{e.id},{e.date},{e.category},{e.amount},{e.description}\n" for e in expenses
            )


class JsonExporter:
    def export(self, expenses: Sequence[Expense], path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in expenses], f, indent=2, ensure_ascii=False)


class TxtExporter:
    def export(self, expenses: Sequence[Expense], path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(
                f"[{e.date}] {e.category:<14} {e.amount:>10.2f}  {e.description}\n"
                for e in expenses
            )
            f.write(f"TOTAL: {_total(expenses):.2f}\n")


def _total(expenses: Sequence[Expense]) -> float:
    # Same left-to-right loop as ExpenseService.total(); sum() is not used because
    # since Python 3.12 it does compensated float summation and could differ.
    total = 0.0
    for e in expenses:
        total += e.amount
    return total


EXPORTERS: dict[str, Exporter] = {
    "csv": CsvExporter(),
    "json": JsonExporter(),
    "txt": TxtExporter(),
}
