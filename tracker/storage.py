import json
import os

from tracker.models import Expense

DEFAULT_FILE = "expenses.json"


class JsonStorage:
    def __init__(self, path=DEFAULT_FILE):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Expense.from_dict(item) for item in data]

    def save(self, expenses):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in expenses], f, indent=2, ensure_ascii=False)
