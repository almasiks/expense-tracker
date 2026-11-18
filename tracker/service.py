import math
from datetime import date

from tracker.exporters import EXPORTERS
from tracker.models import Expense

CATEGORIES = ["food", "transport", "rent", "entertainment", "other"]


def _parse_amount(amount: float | str) -> float:
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError(f"Amount must be a number, got {amount!r}") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"Amount must be a positive finite number, got {amount!r}")
    return value


class ExpenseService:
    def __init__(self, storage):
        self.storage = storage
        self.expenses = storage.load()

    def _next_id(self) -> int:
        return max((e.id for e in self.expenses), default=0) + 1

    def add_expense(
        self,
        amount: float | str,
        category: str,
        description: str = "",
        when: str | None = None,
    ) -> Expense:
        value = _parse_amount(amount)
        if category not in CATEGORIES:
            category = "other"
        if when is None:
            when = date.today().isoformat()
        expense = Expense(
            id=self._next_id(),
            amount=value,
            category=category,
            description=description,
            date=when,
        )
        self.expenses.append(expense)
        self.storage.save(self.expenses)
        return expense

    def delete_expense(self, expense_id):
        for e in self.expenses:
            if e.id == expense_id:
                self.expenses.remove(e)
                self.storage.save(self.expenses)
                return True
        return False

    def list_expenses(self, category=None, month=None):
        result = self.expenses
        if category:
            result = [e for e in result if e.category == category]
        if month:  # format YYYY-MM
            result = [e for e in result if e.date.startswith(month)]
        return result

    def total(self, category=None, month=None):
        total = 0
        for e in self.list_expenses(category, month):
            total += e.amount
        return total

    def totals_by_category(self, month=None):
        result = {}
        for e in self.list_expenses(month=month):
            result[e.category] = result.get(e.category, 0) + e.amount
        return result

    def export(self, fmt: str, path: str) -> None:
        exporter = EXPORTERS.get(fmt)
        if exporter is None:
            raise ValueError("Unknown format: " + fmt)
        exporter.export(self.expenses, path)
