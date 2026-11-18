# Task 03 — Pattern decision: Strategy for export formats

## 1. Problem (evidence from the baseline)

At tag `baseline` (`07cac1e`) all three export formats live in one method,
`ExpenseService.export()` in `tracker/service.py` lines 60–77:

```python
def export(self, fmt, path):
    expenses = self.expenses
    if fmt == "csv":            # lines 62-66: header + f-string rows
        ...
    elif fmt == "json":         # lines 67-70: local `import json` inside the branch
        ...
    elif fmt == "txt":          # lines 71-75: rows + TOTAL via self.total()
        ...
    else:
        raise ValueError("Unknown format: " + fmt)   # line 77
```

Issues:
- **Mixed responsibilities:** `service.py` holds business logic *and* file-format details
  (column order, padding, JSON options). Every new format means editing this method.
- **Untested:** lines 61–77 were never executed by tests (baseline coverage,
  `evidence/02_coverage.txt`: `service.py 69%, missing 38, 43, 61-77`), see W1 in `docs/01-baseline.md`.
- **Lint:** `ruff check .` flagged `FURB122` at `service.py:65` (`f.write` in a loop) — `evidence/03_ruff.txt`.
- Local `import json` inside a branch (line 68); no type hints.

## 2. Options considered

| Option | Pros | Cons |
|--------|------|------|
| **A. Keep `if/elif`** | Simplest; zero new files; 3 formats is small | Format details stay in the service; adding a format = editing a growing method |
| **B. Strategy** (class per format + shared interface + registry) | Each format isolated and testable on its own; service is closed for modification (new format = new class + one dict entry); interface is typed (`Protocol`) | One new module and a little ceremony (3 small classes) |
| **C. Dict of functions** (`{"csv": export_csv, ...}`) | Same dispatch benefit as B with less code | No named interface; harder to give a format configuration/state later (e.g. CSV delimiter) |

**Decision: B (Strategy)** — but honestly **borderline**. With only three stateless formats,
option C would give almost the same benefit with fewer lines. Strategy was chosen because
the assignment targets a design pattern, the `Exporter` Protocol documents the contract for
mypy, and it leaves room for per-format options without changing the service. If formats had
stayed fixed forever, A would also have been acceptable.

## 3. Before / after structure

Before:
```
tracker/
  service.py   ExpenseService.export(): if/elif over csv | json | txt (18 lines)
```

After:
```
tracker/
  exporters.py  Exporter (Protocol): export(expenses, path) -> None
                CsvExporter, JsonExporter, TxtExporter
                EXPORTERS = {"csv": CsvExporter(), "json": JsonExporter(), "txt": TxtExporter()}
  service.py    def export(self, fmt: str, path: str) -> None:
                    exporter = EXPORTERS.get(fmt)
                    if exporter is None:
                        raise ValueError("Unknown format: " + fmt)
                    exporter.export(self.expenses, path)
```

Dependency direction: `cli -> service -> exporters -> models` (and `service -> storage -> models`).
No changes to `cli.py`, `models.py`, `storage.py`.

Note on byte-identical output: `TxtExporter` computes the total with the same left-to-right
`+=` loop as `ExpenseService.total()` instead of `sum()`, because since Python 3.12 `sum()` uses
compensated float summation and could print a different last digit.

## 4. Test counts and coverage

| | Before refactor (`evidence/07_tests_before_refactor.txt`) | After refactor (`evidence/08_tests_after_refactor.txt`) |
|---|---|---|
| Tests | 12 passed, 0 failed | 12 passed, 0 failed |
| `service.py` | 97% (59 stmts, missing 38, 43) | 96% (48 stmts, missing 39, 44 — same two lines, shifted by the new import) |
| `exporters.py` | — | 100% (25 stmts) |
| TOTAL | 61% (133 stmts) | 65% (147 stmts) |
| `ruff check .` | 3 errors at baseline (`evidence/03_ruff.txt`) | 2 errors — `FURB122` gone; the two `I001` in `cli.py`/`models.py` are untouched, pre-existing |
| `mypy tracker` | Success, 5 files | Success, 6 files |

(Baseline before characterization tests: 7 passed, 49% — `evidence/01_tests.txt`, `evidence/02_coverage.txt`.)

## 5. Acceptance criteria re-verified

- **AC4** (export writes every expense; unknown format raises and writes nothing): now covered
  automatically by `tests/test_export.py` (5 tests, written and committed *before* the refactor
  in `d2e0a2f`, not modified afterwards). They compare exact file bytes for csv/json/txt and
  check `ValueError("Unknown format: xml")` with no file created. In addition, a one-off script
  compared the output of the pre-refactor code (from commit `d2e0a2f`) and the refactored code
  for an empty list and for 6 varied expenses (commas, quotes, newline, Cyrillic, negative and
  tiny amounts): all 6 files were byte-identical (`evidence/08_tests_after_refactor.txt`, last section).
- **AC5** (full suite passes): `python -m pytest -v` → 12 passed, 0 failed, before and after.
- AC1–AC3 are unaffected (no changes to storage, totals or categories) and their tests still pass.
