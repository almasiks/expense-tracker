# Task 01 — Baseline and Context

**Baseline:** commit `07cac1e`, tag `baseline` (https://github.com/almasiks/expense-tracker/tree/baseline)
**Date:** 2026-11-18
**Environment:** Windows 11 Home 10.0.26200 (pytest reports `platform win32`), `Python 3.14.3` (venv `.venv`) — see `evidence/00_python_version.txt`

## 1. Repository map

| Area | Files | Notes |
|------|-------|-------|
| Entry point | `tracker/cli.py` → `main()` | Run as `python -m tracker.cli <command>`; argparse sub-commands `add`, `list`, `delete`, `summary`, `export` |
| Business logic | `tracker/service.py` (`ExpenseService`) | add/delete/list/filter, totals, export (csv/json/txt) |
| Data model | `tracker/models.py` (`Expense` dataclass) | `id, amount (float), category, description, date (str)` |
| Persistence | `tracker/storage.py` (`JsonStorage`) | Reads/writes whole list to `expenses.json` |
| Tests | `tests/test_service.py` | 7 pytest tests, service + storage only |
| Dependencies | `requirements.txt` | `pytest` (no version) — only dev dependency; app uses stdlib only |
| Build / lint / CI | — | No build step (pure Python), no linter/type-checker config, no CI workflow |
| Docs | `README.md` | Setup, usage, test command |

Dependency flow: `cli.py → service.py → storage.py → models.py`

## 2. Commands and actual results

| # | Purpose | Exact command | Actual result |
|---|---------|---------------|---------------|
| 1 | Install | `pip install -r requirements.txt` | OK — `pytest 9.2.0` installed (unpinned; whatever was latest). Later `pip install pytest-cov ruff mypy` → `pytest-cov 7.1.0`, `coverage 7.17.3`, `ruff 0.17.5`, `mypy 2.4.1` |
| 2 | Tests | `python -m pytest -v` | `7 passed in 0.06s`, 0 failed (`evidence/01_tests.txt`) |
| 3 | Coverage | `pip install pytest-cov` then `python -m pytest --cov=tracker --cov-report=term-missing` | 7 passed; **TOTAL 49%** (133 stmts, 68 missed): `cli.py` 0% (missing 1-65), `service.py` 69% (missing 38, 43, 61-77), `models.py` 100%, `storage.py` 100%, `__init__.py` 100% (`evidence/02_coverage.txt`) |
| 4 | Lint | `pip install ruff` then `ruff check .` | **Found 3 errors** (exit code 1), all `[*]` auto-fixable: `I001` unsorted imports in `tracker/cli.py:1` and `tracker/models.py:1`; `FURB122` `f.write` in a loop in `tracker/service.py:65`. Ruff default rules (same result with `--isolated`, no config in repo) (`evidence/03_ruff.txt`) |
| 5 | Type check | `pip install mypy` then `mypy tracker` | `Success: no issues found in 5 source files` (`evidence/04_mypy.txt`) |
| 6 | Build | n/a — pure Python, no packaging (`pyproject.toml` absent) | not applicable |
| 7 | Smoke run | `python -m tracker.cli --file demo.json add 1500 food -d lunch`, then `... add -500 food`, then `... summary` | `Added #1: 1500.00 (food)` / `Added #2: -500.00 (food)` / `food 1000.00` / `TOTAL 1000.00` (`evidence/05_smoke_negative_amount.txt`; `demo.json` deleted afterwards) |

Evidence: raw command outputs in evidence/*.txt

## 3. Weaknesses / missing checks (with evidence)

| ID | Weakness | Evidence (file / command) |
|----|----------|---------------------------|
| W1 | CLI layer and export are not tested: `cli.py` has 0% coverage, `export()` lines are never executed by tests. Coverage also shows two more untested branches in `service.py`: line 38 (`delete_expense` returning `False` for a non-existent id) and line 43 (the `category` filter in `list_expenses`). | Command #3 output: `tracker\cli.py 50 50 0% 1-65`; `tracker\service.py 59 18 69% 38, 43, 61-77` (61-77 = `export`) |
| W2 | No lint / type-check / CI configured in the repo — quality checks are not part of the workflow. | No `pyproject.toml`, `ruff.toml`, `mypy.ini` or `.github/workflows/` in repo; tools had to be installed manually (commands #4, #5) |
| W3 | Dependencies are not pinned: `pytest` has no version, so installs are not reproducible. | `requirements.txt` line 1: `pytest` |
| W4 | No input validation: a negative amount is accepted and reduces totals. | `python -m tracker.cli --file demo.json add -500 food` → `Added #2: -500.00 (food)`; `summary` then shows `TOTAL 1000.00` instead of 1500.00 (`evidence/05_smoke_negative_amount.txt`) |

## 4. Facts vs. assumptions

**Observed facts** (I ran these myself): results in table §2, W1–W4 evidence above.

**Assumptions (not verified):**
- The app is used by one person at a time (no concurrent writes considered).
- Amounts are in a single currency (KZT); no currency field exists.

**Unverified AI suggestions** (to be investigated in Task 04, not counted as facts yet):
- mypy passes only because no function in `tracker/` has type annotations, so mypy does not check their bodies by default; with `--check-untyped-defs` it reportedly finds 1 error (`service.py:55`, `var-annotated`).
- CSV export (`service.py:66`) builds rows with an f-string and no quoting, so a description containing a comma or newline would likely corrupt the CSV.
- Resolved: AC2 corrected — `ACCEPTANCE.md` now states the `--category` filter has no automated test at baseline (`service.py:43` never executed).
- Ruff's 3 findings are style-only (`I001`, `FURB122`) and auto-fixable; they are not believed to indicate bugs.
