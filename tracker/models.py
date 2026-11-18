from dataclasses import dataclass, asdict


@dataclass
class Expense:
    id: int
    amount: float
    category: str
    description: str
    date: str  # YYYY-MM-DD

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Expense(
            id=data["id"],
            amount=data["amount"],
            category=data["category"],
            description=data["description"],
            date=data["date"],
        )
