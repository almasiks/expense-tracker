# AGENTS.md — Expense Tracker

Instructions for AI coding agents (Claude Code, Codex, etc.) working in this repo.

## Purpose

A small command-line app for tracking personal expenses. Users add, list, delete,
summarize and export expenses; data is stored in a local JSON file. Pure Python, stdlib only.

## Architecture

Dependency direction (one way only — never import "upwards"):

```
tracker/cli.py  ->  tracker/service.py  ->  tracker/storage.py    ->  tracker/models.py
                                        ->  tracker/exporters.py  ->  tracker/models.py
```

| Module | Responsibility |
|--------|----------------|
| `cli.py` | argparse parsing (`add`, `list`, `delete`, `summary`, `export`), printing. No business rules. |
| `service.py` | `ExpenseService` + `CATEGORIES`: all business logic — validation, category fallback to `other`, filtering, totals; `export()` picks a strategy from `EXPORTERS`. |
| `exporters.py` | Strategy for export formats: `Exporter` Protocol, `CsvExporter`, `JsonExporter`, `TxtExporter`, `EXPORTERS` registry. |
| `storage.py` | `JsonStorage`: load/save the whole list to a JSON file (default `expenses.json`). |
| `models.py` | `Expense` dataclass (`id, amount, category, description, date`) and dict conversion. |

- New business logic goes in `service.py`, not `cli.py`. The CLI only parses args, calls the service, prints.
- `service.py` must not print or read `sys.argv`; `storage.py` must not contain business rules.
- New export formats: add a new exporter class in `exporters.py` + an `EXPORTERS` entry
  (with a test in `tests/test_export.py`) — never a new `if/elif` branch in `service.py`.

## Setup

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dev tools (`pytest-cov`, `ruff`, `mypy`) are not in `requirements.txt`; installing them needs approval (see below).

## Safe commands (allowed without asking)

- `python -m pytest -v`
- `python -m pytest --cov=tracker --cov-report=term-missing`
- `ruff check .` (check only — `--fix` changes files, so treat it as an edit)
- `mypy tracker`
- `git status`, `git diff`, `git log`
- The CLI **only** with `--file` pointing to a temp/demo file, e.g.
  `python -m tracker.cli --file demo.json add 1500 food -d lunch`, then delete `demo.json`.
  Without `--file` the CLI writes to the real `expenses.json` — never do that.

## Needs human approval first

- `pip install ...` or any change to `requirements.txt`
- `git commit`, `git push`
- Deleting any file (except a demo file you created yourself in this session)
- Editing `ACCEPTANCE.md`

## Forbidden

- Committing secrets, `.env` files or real personal data (including any real `expenses.json`).
- Production deployment of any kind.
- Destructive commands: `rm -rf`, `git push --force`, `git reset --hard`, `git clean -fd`,
  rewriting history, moving or deleting the `baseline` tag.
- Adding or upgrading dependencies without review.
- Writing to the real `expenses.json`.
- Disabling, skipping, deleting or weakening tests to make them pass.
- Fabricating, editing or summarizing-away test/tool output. Report what actually ran.

## Coding conventions

- Python 3 (developed on 3.14), PEP 8, `ruff check .` clean for any lines you touch.
- Small, single-purpose functions; keep the module boundaries above.
- No new third-party runtime dependencies — stdlib only.
- Type hints for all new or changed functions.
- File I/O uses `encoding="utf-8"`. Dates are ISO strings: `YYYY-MM-DD`, months `YYYY-MM`.

## Test expectations

- Every behavior change needs a test in `tests/` (pytest; use the `tmp_path` fixture,
  never the real data file).
- The full suite must pass — `python -m pytest -v` reports **0 failed** — before any commit.
- Acceptance criteria AC1–AC5 in `ACCEPTANCE.md` must still hold after every change.
- Report exact counts from the real run (e.g. `8 passed, 0 failed in 0.07s`), not "tests pass".
- Baseline (tag `baseline`): 7 passed, coverage 49% (`cli.py` 0%), ruff 3 findings, mypy clean.
  Known weaknesses W1–W4 are listed in `docs/01-baseline.md`; do not make these numbers worse.

## Review gates / definition of done

A change is done only when:
1. It is one focused change (one concern per commit).
2. Tests for the new/changed behavior exist and the full suite passes (0 failed).
3. `ruff check .` and `mypy tracker` show no new issues vs. baseline.
4. AC1–AC5 still hold.
5. You have shown the human the `git diff` and the real test output.
6. The human has approved — only then commit. Push is a separate approval.
