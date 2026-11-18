import pytest

from tracker.cli import main
from tracker.storage import JsonStorage


@pytest.mark.parametrize("amount", ["-500", "0", "nan", "inf", "abc", "1,5"])
def test_add_invalid_amount_prints_error_and_exits_1(tmp_path, capsys, amount):
    path = tmp_path / "data.json"

    exit_code = main(["--file", str(path), "add", amount, "food"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err.startswith("Error: Amount must be")
    assert "Traceback" not in captured.err + captured.out
    assert not path.exists()


def test_add_valid_amount_exits_0(tmp_path, capsys):
    path = tmp_path / "data.json"

    exit_code = main(["--file", str(path), "add", "1500", "food", "-d", "lunch"])

    assert exit_code == 0
    assert capsys.readouterr().out == "Added #1: 1500.00 (food)\n"
    assert len(JsonStorage(str(path)).load()) == 1
