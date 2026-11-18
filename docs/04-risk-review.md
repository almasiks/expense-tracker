# Task 04 — AI risk review and verification

- **Phase 1** (read-only): an AI agent proposed 8 candidate risks R1–R8 → `evidence/09_ai_risk_proposals_raw.txt`.
- **Phase 2** (verification): each claim was reproduced with real commands at commit `1c45896`,
  in a fresh temp directory (CLI always run with `--file` or with cwd = temp dir; the real
  `expenses.json` was never touched; `tracker/` and `tests/` not modified) → raw output in
  `evidence/10_risk_verification.txt`, section headers `R1` … `R8`.

Classification: **CONFIRMED** = reproduced, real output cited · **PLAUSIBLE/UNVERIFIED** = reasonable,
not reproduced · **UNSUPPORTED** = evidence contradicts it. Composite risks are split into sub-claims.

## Results

| ID | Category | Claim | Classification | Evidence |
|----|----------|-------|----------------|----------|
| R1 | correctness | `_next_id()` = `len+1` (`service.py:14-15`) gives duplicate IDs after delete; `delete N` removes only the first match | **CONFIRMED** | add 100/200/300, `delete 1`, add 400 → `Added #3: 400.00`; `list` shows `#3 … 300.00` and `#3 … 400.00`; `delete 3` removed the 300 row, the 400 row stays as `#3` |
| R2a | correctness | Negative and zero amounts accepted (`service.py:24`) | **CONFIRMED** | `add -500 food` → `Added #1: -500.00`; `add 0 food` → `Added #2: 0.00` |
| R2b | correctness | `nan` / `inf` / `1e309` accepted; totals become `nan`; file gets non-standard JSON | **CONFIRMED** | `Added #3: nan`, `Added #4: inf`, `Added #5: inf`; `summary` → `TOTAL nan`; `r2.json` contains `"amount": NaN` and `Infinity`; strict parse → `ValueError: non-standard JSON constant: NaN` |
| R2c | correctness | `1,5` crashes with an uncaught traceback | **CONFIRMED** | `ValueError: could not convert string to float: '1,5'` at `service.py:24`, exit 1 |
| R3a | correctness | Dates not validated (`service.py:20-21`) | **CONFIRMED** | `--date hello` and `--date 2026-13-99` both stored; `list` prints `hello` and `2026-13-99` |
| R3b | correctness | `--month` uses prefix match (`service.py:46`), so `2026-1` matches other months | **CONFIRMED**, but the AI's predicted output was **wrong** | Data: 10 on `2026-01-05`, 1000 on `2026-11-05`. `summary --month 2026-1` → `TOTAL 1000.00` (November only — January is **not** included, contrary to the AI's "expect both to be counted"). `--month 2026-01` → `TOTAL 10.00` |
| R4a | correctness / data integrity | `export csv <data file>` overwrites the data file; every later command crashes | **CONFIRMED** | `export csv r4.json` → file now `id,date,category,amount,description…`; `list` → `json.decoder.JSONDecodeError: Expecting value` at `storage.py:17`, exit 1 |
| R4b | correctness / data integrity | Non-atomic `save()` (`storage.py:20-22`): an interruption during write empties the file | **CONFIRMED** (simulated) | `json.dump` monkeypatched to raise `KeyboardInterrupt` → `file size after interrupted save: 0 bytes`; next `list` → `JSONDecodeError`. Simulated interruption, not a real crash/power loss |
| R5a | security / integrity | CSV rows built without quoting (`exporters.py:21-23`): a comma in the description shifts columns | **CONFIRMED** | `-d "a,b"` → `csv.reader` returns `6 ['1', …, 'a', 'b']` vs. 5-field header |
| R5b | security | A `"` in the description also breaks columns | **UNSUPPORTED** (for the tested case) | `-d 'say "hi"'` → `csv.reader` returns 5 fields correctly. A quote at the *start* of a field and a newline in the description were not tested |
| R5c | security | Formula injection: `=…` runs as a formula in Excel/Sheets | **PLAUSIBLE / UNVERIFIED** | Confirmed only that `=1+1` is written unescaped (`2,2026-11-18,food,1.0,=1+1`); not opened in a spreadsheet |
| R6a | dependency | `requirements.txt` has only unpinned `pytest`; `pytest-cov`, `ruff`, `mypy` are declared nowhere; no Python version declared | **CONFIRMED** | `cat requirements.txt` → `pytest`; no `pyproject.toml`/`setup.*` in `ls -a`; grep for `pytest-cov|ruff|mypy|requires-python` in requirements/README → no match (exit 1). Working venv has unrecorded `ruff==0.17.5`, `mypy==2.4.1`, `pytest-cov==7.1.0` (`pip freeze`) |
| R6b | dependency | Other tool versions give different lint/type results, so baseline numbers are not reproducible | **PLAUSIBLE / UNVERIFIED** | No second ruff/mypy version installed (installs need approval per `AGENTS.md`) |
| R6c | dependency | Code requires Python ≥ 3.9 | **PLAUSIBLE / UNVERIFIED** | Uses `dict[str, Exporter]` at module level and `collections.abc.Sequence` (`exporters.py:8, 52`); only 3.11/3.12/3.14 installed (`py -0p`), so an older interpreter was not tested |
| R7a | maintainability | Duplicated logic/config: total loop in two places, default file name in two places | **CONFIRMED** | `service.py:50,52` and `exporters.py:46,48`; `"expenses.json"` in `cli.py:9` and `DEFAULT_FILE` in `storage.py:6` (not used by `cli.py`) |
| R7b | maintainability | The two total implementations can disagree (TXT `TOTAL:` vs `summary`) | **UNSUPPORTED** (currently) | 2000 random expense sets (incl. 0.1/0.2/0.3, ±1e16, 1/3) → `mismatches = 0`. Only a future-divergence risk, not a present defect |
| R7c | maintainability | Core is untyped, so mypy "checks almost nothing" | **CONFIRMED** that bodies are skipped; "almost nothing" **overstated** | Only `export()` in `service.py` has hints (line 61). `mypy` → Success; `mypy --check-untyped-defs` → 1 error `service.py:56 [var-annotated]`. `exporters.py`/`models.py` *are* fully checked |
| R7d | maintainability | CLI untested | **CONFIRMED** | coverage: `tracker\cli.py 50 50 0% 1-65` |
| R8a | agent ops | Without `--file` the CLI writes `./expenses.json` in the cwd | **CONFIRMED** | in an empty dir: `summary` creates no file; `add 1 food` → `ls` shows `expenses.json` |
| R8b | agent ops | Demo/export/custom data files are not git-ignored → could be committed | **CONFIRMED** (gap); actual leak not shown | `git check-ignore -v` matches only `expenses.json` (`.gitignore:5`) and `r.csv` (`.gitignore:6`); `demo.json`, `report.txt`, `my.json` are not ignored. Note: the *default* `expenses.json` **is** ignored, so R8a alone does not leak data via git |
| R8c | agent ops | Rules are prose only — no CI, pre-commit or git hooks | **CONFIRMED** | `.github` and `.pre-commit-config.yaml` do not exist; `.git/hooks` contains only `*.sample` files |
| R8d | agent ops | Claude loads the rules only via the `@AGENTS.md` import in `CLAUDE.md` | **PLAUSIBLE / UNVERIFIED** | `CLAUDE.md` contains the import (`cat`). `evidence/06_agent_instructions_loaded.txt` lists the rules correctly, but it is **not** fresh-session evidence: its first line says *"I'm answering from AGENTS.md, which I wrote earlier in this conversation and still have in context"* — it was answered in the same long session that wrote AGENTS.md, so it cannot show the import works. Needs a new session (with and without the import) |

**Summary (22 sub-claims):** 16 CONFIRMED (2 of them — R3b, R7c — with a wrong/overstated detail), 4 PLAUSIBLE/UNVERIFIED (R5c, R6b, R6c, R8d), 2 UNSUPPORTED (R5b, R7b).

## Where the AI was wrong or overstated

1. **R3 — wrong predicted output.** The AI said `summary --month 2026-1` would count both the
   January and the November expense. In reality it counted **only November** (`TOTAL 1000.00`):
   `"2026-01-05"` does not start with `"2026-1"`. The bug is real (prefix match catches
   2026-10/11/12), but the AI's described symptom was incorrect.
2. **R5 — `"` does not break columns** in the tested case (`say "hi"` parsed as 5 fields). The AI
   listed `,`, `"` and newline together; only `,` was reproduced. Formula injection was asserted
   as a "security" risk without any spreadsheet test; for a single-user local tool its severity is
   likely overstated — the reproduced problem is data integrity, not security.
3. **R7 — divergence of the two total loops is not happening now** (0 mismatches in 2000 sets),
   and "mypy checks almost nothing" is overstated: `exporters.py` and `models.py` are fully
   checked, and even `--check-untyped-defs` finds just one annotation issue.
4. **R8 — partly overstated.** "Running without `--file` writes the real data file" is true, but
   that file is git-ignored, so it does not by itself lead to a committed data leak; the leak path
   requires a non-default file name. Whether Claude would lose the rules without the import was
   never tested; `evidence/06` was produced in the same session that wrote AGENTS.md (it says so
   in its first line), so it does not count as proof that the `@AGENTS.md` import loads the rules.
5. **R6 — only the static facts are proven.** Version-drift consequences and the Python ≥ 3.9
   requirement are reasonable but were not reproduced.

Strongest, fully reproduced risks for follow-up: **R4** (data loss), **R1** (duplicate IDs),
**R2** (amount validation), **R3b** (month filter).
