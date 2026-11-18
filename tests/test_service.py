import pytest

from tracker.service import ExpenseService
from tracker.storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return ExpenseService(JsonStorage(str(tmp_path / "data.json")))


def test_add_expense(service):
    e = service.add_expense(1500, "food", "lunch", "2026-11-01")
    assert e.id == 1
    assert e.amount == 1500
    assert len(service.list_expenses()) == 1


def test_unknown_category_becomes_other(service):
    e = service.add_expense(100, "games")
    assert e.category == "other"


def test_total(service):
    service.add_expense(1000, "food", when="2026-11-01")
    service.add_expense(500, "transport", when="2026-11-02")
    assert service.total() == 1500


def test_filter_by_month(service):
    service.add_expense(1000, "food", when="2026-10-15")
    service.add_expense(2000, "food", when="2026-11-03")
    assert service.total(month="2026-11") == 2000


def test_totals_by_category(service):
    service.add_expense(1000, "food", when="2026-11-01")
    service.add_expense(300, "food", when="2026-11-02")
    service.add_expense(700, "rent", when="2026-11-02")
    assert service.totals_by_category() == {"food": 1300, "rent": 700}


def test_data_is_saved(tmp_path):
    path = str(tmp_path / "data.json")
    ExpenseService(JsonStorage(path)).add_expense(250, "transport")
    reloaded = ExpenseService(JsonStorage(path))
    assert reloaded.total() == 250


def test_delete(service):
    e = service.add_expense(100, "food")
    assert service.delete_expense(e.id) is True
    assert service.list_expenses() == []


def _ids(service: ExpenseService) -> list[int]:
    return [e.id for e in service.list_expenses()]


@pytest.mark.parametrize("deleted_id", [2, 1])
def test_new_id_is_unique_after_delete(service, deleted_id):
    # deleted_id=1 reproduces evidence/10, section "R1 duplicate IDs after delete"
    for amount in (100, 200, 300):
        service.add_expense(amount, "food")
    service.delete_expense(deleted_id)

    new = service.add_expense(400, "food")

    assert new.id == 4
    assert len(_ids(service)) == len(set(_ids(service)))


@pytest.mark.parametrize("deleted_id", [2, 1])
def test_delete_new_record_removes_exactly_that_record(tmp_path, deleted_id):
    path = str(tmp_path / "data.json")
    service = ExpenseService(JsonStorage(path))
    for amount in (100, 200, 300):
        service.add_expense(amount, "food")
    service.delete_expense(deleted_id)
    new = service.add_expense(400, "food")

    assert service.delete_expense(new.id) is True

    reloaded = ExpenseService(JsonStorage(path))
    remaining = sorted(e.amount for e in reloaded.list_expenses())
    expected = sorted({100, 200, 300} - {deleted_id * 100})
    assert remaining == expected
