# Task 07 — Mitigations for R1 and R2

Risks come from `docs/05-risk-register.md`. Each one was fixed red → green: the targeted tests were written
first and failed on the old code, then the minimal fix was applied and the full suite was run.
One commit per risk. All numbers below are copied from the evidence files and were not re-typed from memory.

| Risk | Commit | Red evidence | Green evidence |
|------|--------|--------------|----------------|
| R1 duplicate IDs | `234aeef` Task 07: mitigate R1 duplicate IDs | `evidence/11_R1_red.txt` — **4 failed, 12 passed** | `evidence/12_R1_green.txt` — **16 passed, 0 failed** |
| R2 amount validation | `016cf32` Task 07: mitigate R2 amount validation | `evidence/13_R2_red.txt` — **21 failed, 19 passed** | `evidence/14_R2_green.txt` — **40 passed, 0 failed** + CLI smoke run |
| Final checks | — (HEAD `016cf32`) | — | `evidence/15_final_checks.txt` |

## R1 — duplicate IDs after delete

**Change:** `tracker/service.py` → `ExpenseService._next_id`

```diff
-    def _next_id(self):
-        return len(self.expenses) + 1
+    def _next_id(self) -> int:
+        return max((e.id for e in self.expenses), default=0) + 1
```

**Diff summary:** 2 files, +36 / −2. One line of logic plus a return type hint. Tests were added in
`tests/test_service.py`. Both are parametrized over `deleted_id ∈ {2, 1}`; `1` is the exact case reproduced in
`evidence/10`, section "R1 duplicate IDs after delete".

- `test_new_id_is_unique_after_delete` — add 3, delete one, add → new id is `4` and all ids are unique.
- `test_delete_new_record_removes_exactly_that_record` — deleting the new record removes only that record.
  The test reloads the data from the file.

**Red:** `assert 3 == 4` (duplicate id 3). `assert [100.0, 400.0] == [100, 300]`: deleting the new record
removed the old #3 instead. Note: a first draft of the delete test (it deleted id `3`) **passed** on the buggy
code, so it was rewritten before the red evidence was saved.

**Green:** 16 passed, 0 failed. ruff: 2 findings (both pre-existing, see the table below). mypy clean.

## R2 — amount validation

**Change:**
- `tracker/service.py` → new `_parse_amount(amount) -> float`, called first in `ExpenseService.add_expense`
  (before anything is appended or saved). Messages:
  - `Amount must be a number, got 'abc'` — `float()` failed (`abc`, `1,5`, empty string).
  - `Amount must be a positive finite number, got '-500'` — ≤ 0, `nan`, `inf`, `-inf`, `1e309`.
- `tracker/cli.py` → `main`: for `add` it catches `ValueError`, prints `Error: <message>` to **stderr** and
  returns `1`. Otherwise it returns `0`. `__main__` runs `sys.exit(main())`, so the process exit code is real.
  Signature: `main(argv: list[str] | None = None) -> int`.
  The import block was reordered (`CATEGORIES, ExpenseService`) because adding `import sys` touched it and
  AGENTS.md requires touched lines to be ruff-clean.

**Diff summary:** 4 code/test files, +66 / −6, plus evidence 13 and 14.

- `tests/test_service.py::test_invalid_amount_is_rejected_and_nothing_saved` — 14 parametrized amounts
  (`-1, -500, 0, "0", "-0.5", nan, "nan", inf, "inf", "-inf", "1e309", "abc", "1,5", ""`). Each expects
  `ValueError` matching `Amount must be`, and checks that both the in-memory list and the reloaded file still
  hold exactly the 1 valid record added first.
- `tests/test_service.py::test_valid_amount_is_accepted` — `1500`, `"1500.50"`, `"0.01"`. These are guards
  and pass on both red and green.
- `tests/test_cli.py` (new) — `main(["--file", <tmp_path>, "add", amount, "food"])` for
  `-500, 0, nan, inf, abc, 1,5`. Each checks exit code `1`, that stderr starts with `Error: Amount must be`,
  no `Traceback`, and no data file created. There is also one valid-add test: exit code `0`, exact stdout
  line, 1 record saved.

**Red:**
- 11× `DID NOT RAISE ValueError`.
- 3× `Regex pattern did not match`: the raw `could not convert string to float` error.
- CLI: `assert None == 1` for 4 cases, and a raw `ValueError` traceback for `abc` / `1,5`.
- `assert None == 0` for the valid add, because `main` returned nothing.

**Green:** 40 passed, 0 failed. CLI smoke run (demo file in the session scratchpad, deleted afterwards): all
7 invalid amounts print `Error: …` with `[exit 1]`. `add 1500 food` prints `Added #1: 1500.00 (food)`,
`[exit 0]`.

## AC1–AC5 re-check (after both commits, `evidence/15_final_checks.txt`)

| AC | Result | Evidence |
|----|--------|----------|
| AC1 saved and survives restart | Holds | `test_data_is_saved` PASSED. The new R1/R2 tests also reload from the file. `test_add_valid_amount_exits_0` checks the file through the CLI |
| AC2 totals and filters | Holds (same gap as before) | `test_total`, `test_totals_by_category`, `test_filter_by_month` PASSED. The `--category` filter **still has no automated test**: `service.py:62` is uncovered |
| AC3 unknown category → `other` | Holds | `test_unknown_category_becomes_other` PASSED |
| AC4 export | Holds | all 5 `tests/test_export.py` tests PASSED; exporters 100% |
| AC5 suite passes | Holds | `40 passed in 0.44s`, 0 failed |

## Scores before / after (L × I, legend in `docs/05-risk-register.md`)

| Risk | Before | After | Residual risk |
|------|--------|-------|---------------|
| R1 | 3 × 2 = **6** | 1 × 2 = **2** | New duplicates can no longer be created. But (a) data files written **before** the fix may already contain duplicate ids; they are not repaired, and `delete` still removes the first match in them. (b) Deleting the **highest** id and then adding re-uses that id (max+1). That is not a duplicate, but an old exported report could refer to a different record. L = 1 because both need an old file or a specific sequence; I stays 2 (wrong record) |
| R2 | 2 × 2 = **4** | 1 × 2 = **2** | Only `add_expense` validates. `JsonStorage.load` accepts whatever is in the file, so old or hand-edited records with `-500`/`NaN` still distort totals. Very large finite amounts (e.g. `1e300`) are accepted. `1,5` (comma decimal) is rejected with a clear message, not parsed. Refunds/negative entries are intentionally unsupported (owner decision) |

The register planned 1 × 1 for both. 1 × 2 is reported because the legacy-data cases above can still
produce wrong numbers or a wrong-record delete, which is impact 2 under the legend.

## Baseline vs final

Baseline = tag `baseline` (`docs/01-baseline.md`, `evidence/01–04`). Before Task 07 = commit `9f701e1`,
measured at the start of this task. Final = `evidence/15_final_checks.txt` (HEAD `016cf32`).

| Metric | Baseline | Before Task 07 | Final |
|--------|----------|----------------|-------|
| Tests | 7 passed, 0 failed | 12 passed, 0 failed | **40 passed, 0 failed** |
| Coverage TOTAL | 49% (133 stmts, 68 missed) | 65% (147 / 52) | **87% (163 stmts, 22 missed)** |
| `cli.py` | 0% (missing 1-65) | 0% | **64%** (missing 46-66, 71: `list`/`delete`/`summary`/`export` branches, `__main__`) |
| `service.py` | 69% (missing 38, 43, 61-77) | 96% (missing 39, 44) | **97%** (missing 57 = `delete` returns `False`, 62 = category filter) |
| `exporters.py` | — (module did not exist) | 100% | 100% |
| `models.py` | 100% | 100% | 100% |
| `storage.py` | 100% | 100% | 100% |
| ruff | 3 findings (I001 ×2, FURB122) | 2 (I001 `cli.py:1`, `models.py:1`) | **1** (I001 `models.py:1`, pre-existing, untouched) |
| mypy | Success, 5 source files | Success, 6 files | **Success, 6 source files** |

## Not executed / limitations

- **One interpreter, one OS:** everything ran on Python 3.14.3 / Windows 11 (`platform win32`). Python 3.11
  and 3.12 are installed (`py -0p`, `evidence/10`) but the suite was **not** run on them. There was no
  Linux/macOS run.
- **No CI:** no GitHub Actions or pre-commit hook ran these checks. The evidence is from local runs only
  (R8c still open).
- **No spreadsheet check:** no real Excel / Google Sheets was opened. CSV behavior (R5a/R5c) was not
  touched by this task.
- **CLI coverage is partial:** `list`, `delete`, `summary` and `export` are still not tested through
  `main()` (`cli.py` 64%). The stderr-vs-stdout choice for `Error:` is pinned only by `tests/test_cli.py`.
- **No legacy-data test:** no test or migration for data files that already contain duplicate ids or
  invalid amounts (see residual risk).
- **Not stress-tested:** no concurrent access, no interruption during `save()` (R4), no fresh-clone install
  from `requirements.txt` (R6a).
- **Tool settings:** mypy ran with default settings only (no `--check-untyped-defs` / `--strict`). ruff ran
  with default rules only. Coverage is line coverage, not branch coverage.
- **Garbled path in evidence:** in `evidence/15_final_checks.txt` the `rootdir:` path is mojibake
  (Cyrillic folder name through the Windows console encoding). This is cosmetic; the counts are unaffected.
