from datetime import date

from tracker.models import Expense

CATEGORIES = ["food", "transport", "rent", "entertainment", "other"]


class ExpenseService:
    def __init__(self, storage):
        self.storage = storage
        self.expenses = storage.load()

    def _next_id(self):
        return len(self.expenses) + 1

    def add_expense(self, amount, category, description="", when=None):
        if category not in CATEGORIES:
            category = "other"
        if when is None:
            when = date.today().isoformat()
        expense = Expense(
            id=self._next_id(),
            amount=float(amount),
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

    def export(self, fmt, path):
        expenses = self.expenses
        if fmt == "csv":
            with open(path, "w", encoding="utf-8") as f:
                f.write("id,date,category,amount,description\n")
                for e in expenses:
                    f.write(f"{e.id},{e.date},{e.category},{e.amount},{e.description}\n")
        elif fmt == "json":
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in expenses], f, indent=2, ensure_ascii=False)
        elif fmt == "txt":
            with open(path, "w", encoding="utf-8") as f:
                for e in expenses:
                    f.write(f"[{e.date}] {e.category:<14} {e.amount:>10.2f}  {e.description}\n")
                f.write(f"TOTAL: {self.total():.2f}\n")
        else:
            raise ValueError("Unknown format: " + fmt)
