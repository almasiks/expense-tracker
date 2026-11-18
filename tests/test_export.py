"""Characterization tests for ExpenseService.export().

They pin down the CURRENT (baseline) behavior byte-for-byte, including quirks
such as CSV rows without quoting, so that a refactoring cannot change output.
"""

import json
import os

import pytest

from tracker.service import ExpenseService
from tracker.storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    s = ExpenseService(JsonStorage(str(tmp_path / "data.json")))
    s.add_expense(1500, "food", "lunch", "2026-11-01")
    s.add_expense(300.5, "transport", "обед, такси", "2026-11-02")
    return s


def read_exact(path):
    """Return file bytes decoded as UTF-8, without newline translation."""
    return path.read_bytes().decode("utf-8")


def native(text):
    """Text-mode files are written with the platform line separator."""
    return text.replace("\n", os.linesep)


def test_export_csv_exact_format(service, tmp_path):
    out = tmp_path / "out.csv"
    service.export("csv", str(out))
    expected = (
        "id,date,category,amount,description\n"
        "1,2026-11-01,food,1500.0,lunch\n"
        "2,2026-11-02,transport,300.5,обед, такси\n"  # current behavior: no quoting
    )
    assert read_exact(out) == native(expected)


def test_export_json_loads_back_to_same_dicts(service, tmp_path):
    out = tmp_path / "out.json"
    service.export("json", str(out))
    with open(out, encoding="utf-8") as f:
        data = json.load(f)
    assert data == [e.to_dict() for e in service.list_expenses()]


def test_export_json_exact_format(service, tmp_path):
    out = tmp_path / "out.json"
    service.export("json", str(out))
    expected = json.dumps(
        [e.to_dict() for e in service.list_expenses()], indent=2, ensure_ascii=False
    )
    assert read_exact(out) == native(expected)
    assert "обед" in read_exact(out)  # non-ASCII is not escaped


def test_export_txt_lines_and_total(service, tmp_path):
    out = tmp_path / "out.txt"
    service.export("txt", str(out))
    expected = (
        "[2026-11-01] food              1500.00  lunch\n"
        "[2026-11-02] transport          300.50  обед, такси\n"
        "TOTAL: 1800.50\n"
    )
    assert read_exact(out) == native(expected)


def test_export_unknown_format_raises_and_creates_no_file(service, tmp_path):
    out = tmp_path / "out.xml"
    with pytest.raises(ValueError, match="Unknown format: xml"):
        service.export("xml", str(out))
    assert not out.exists()
