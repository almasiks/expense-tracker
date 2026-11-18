# Task 06 — Readiness audit

**Scope:** code at commit `016cf32` (Task 07 R1/R2 fixes included), pushed: `origin/main` == `main` ==
`156a527`, which adds only the Task 07 records on top.
**Method:** I read the repo files and used **only evidence that already exists** in `evidence/` and `docs/`.
No new commands were run for this audit. Where no evidence exists, the row says so instead of guessing.
`evidence/10` = `evidence/10_risk_verification.txt` (run on `1c45896`, before Task 07);
`evidence/15` = `evidence/15_final_checks.txt` (run on `016cf32`).

## 1. Readiness criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Readable structure | **Met** | 5 small modules with a one-way dependency chain (`AGENTS.md` § Architecture; `docs/01-baseline.md` §1). Export uses a Strategy registry (`tracker/exporters.py`, `docs/03-pattern-decision.md`). Small deviation: `service.py` also imports `models.py` directly, which the AGENTS.md diagram does not show (`tracker/service.py:5`) |
| 2 | README accuracy | **Partial** | See §2. The commands match the current argparse definitions in `tracker/cli.py`. But the README does not mention the `json`/`txt` export formats, the `--file` option, the new amount rules or the `Error: …`/exit 1 behavior (Task 07), or the Python version. `pytest` differs from the AGENTS.md command `python -m pytest -v` |
| 3 | Reproducible setup | **Missing** | No Python version is declared anywhere. Dev tools are not declared: `grep … pytest-cov\|ruff\|mypy\|python_requires` → no match, exit 1 (`evidence/10` § R6). A fresh venv install was **never run** (`evidence/10`, closing NOTE). Risk R6a |
| 4 | Pinned dependencies | **Missing** | `requirements.txt` = `pytest` (no version). The versions actually used are only visible through `pip freeze` (`pytest==9.2.0`, `pytest-cov==7.1.0`, `ruff==0.17.5`, `mypy==2.4.1`; `evidence/10` § R6). W3 in `docs/01-baseline.md` |
| 5 | Tests | **Met (with gaps)** | `40 passed in 0.44s`, 0 failed. Coverage 87%; `cli.py` 64%, `service.py` 97% (`evidence/15`). Gaps: CLI `list`/`delete`/`summary`/`export` are not tested through `main()` (`cli.py` 46-66). The `--category` filter has no automated test (`service.py:62`, AC2). There are no tests for `storage.py` failure paths (R4) |
| 6 | Lint / type checks | **Partial** | ruff `Found 1 error` (I001 `models.py:1`), mypy `Success: no issues found in 6 source files` (`evidence/15`). But there is no config in the repo: no `pyproject.toml`/`ruff.toml`/`mypy.ini` (W2). mypy runs with defaults only: `--check-untyped-defs` → 1 error at `service.py:56` (`evidence/10` § R7, pre-Task 07; **not re-run** since) |
| 7 | Build commands | **Met (n/a)** | Pure Python, no packaging step. `pyproject.toml` absent; "not applicable" is recorded in `docs/01-baseline.md` §2 #6 |
| 8 | Logging | **Missing (acceptable for scope)** | `grep logging tracker/` → no match. Diagnostics = `print`. Since Task 07 the `add` error goes to stderr with exit 1 (`evidence/14`). Other failures still end in a traceback: unknown export format raises `ValueError` from `service.export`, which `cli.py` does not catch (code reading, `tracker/cli.py:62-64`); corrupted data file → `JSONDecodeError` (`evidence/10` § R4a) |
| 9 | Security safeguards | **Partial** | `.gitignore` ignores `expenses.json` and `*.csv` only. `demo.json`, `report.txt`, `my.json` are **not** ignored (`git check-ignore`, `evidence/10` § R8). No secrets are used by the app (stdlib only, no network). AGENTS.md forbids committing data or secrets (prose only). CSV export is unquoted (R5a) and formula injection is untested (R5c) |
| 10 | CI | **Missing** | No `.github/`, no `.pre-commit-config.yaml`; `.git/hooks` has `*.sample` only (`evidence/10` § R8). All gates are self-reported (R8c) |
| 11 | Agent instructions | **Partial** | `AGENTS.md` exists and `CLAUDE.md` imports it (`@AGENTS.md`). That the rules load in a *fresh* session is **not proven**: `evidence/06` line 1 says it answered from the same conversation (R8d). Inaccuracies: §3 |

## 2. README commands vs current code

The README commands have no `--file`, so they write to `./expenses.json`. AGENTS.md forbids running them like
that, so none were re-run for this audit. "Evidence" means an equivalent run with `--file` that already exists.

| README command | Matches `tracker/cli.py`? | Existing run evidence | Note |
|----------------|---------------------------|-----------------------|------|
| `add 1500 food -d "lunch"` | Yes | `evidence/14` (`add 1500 food` → `Added #1`, exit 0, on `016cf32`); `evidence/05` (`-d lunch`, baseline) | README does not say amounts must be > 0, or that a bad amount prints `Error: Amount must be …` and exits 1 |
| `add 300 transport --date 2026-11-02` | Yes | `evidence/10` § R3 (`--date 2026-11-05`) | The date is **not validated**: `--date hello` is accepted (R3, open) |
| `list` | Yes | `evidence/10` § R1, R2 | — |
| `list --month 2026-11` | Yes | **None.** Only `summary --month` was run (`evidence/10` § R3) | `--month 2026-1` silently matches Oct–Dec (R3) |
| `summary` | Yes | `evidence/10` § R2, R3 | — |
| `delete 1` | Yes | `evidence/10` § R1 (pre-fix) | Not re-run after Task 07; the fix is covered by `tests/test_service.py`. `delete` of a missing id prints "not found" but exits 0 (code reading, `cli.py:52-56`) |
| `export csv report.csv` | Yes | `evidence/10` § R4a, R5 (`export csv r5.csv`) | README omits `json`/`txt`. Exporting onto the data file destroys it (R4a) |
| `pytest` (Tests section) | — | **None** for bare `pytest`. All evidence uses `python -m pytest -v` | Works only if the venv is activated (assumption, not verified) |
| Setup (`venv`, `activate`, `pip install -r requirements.txt`) | — | Only the original baseline install (`docs/01-baseline.md` §2 #1) | Gives unpinned pytest and no ruff/mypy/pytest-cov |

## 3. AGENTS.md inspection

| Section | Present? | Accuracy / gap |
|---------|----------|----------------|
| Permissions (needs approval) | Yes — pip, `requirements.txt`, commit, push, deleting files, editing `ACCEPTANCE.md` | Prose only: no `.claude/settings.json` allow/deny list in the repo, so nothing enforces it |
| Safe commands | Yes — pytest, coverage, `ruff check .`, `mypy tracker`, read-only git, CLI only with `--file` | Accurate. These commands assume dev tools that `requirements.txt` does not provide (stated in the file, but unresolved) |
| Prohibited actions | Yes — secrets/data, deploy, destructive git, dependency changes, real `expenses.json`, weakening tests, fabricating output | Missing the R8 mitigation: "stage by explicit path, never `git add .`/`-A`" was recommended in `docs/05-risk-register.md` but **not added** |
| Review gates / DoD | Yes — 6 steps (one concern, tests, ruff/mypy no regression, AC1–AC5, show diff + output, human approval) | Followed in Task 07 (`evidence/11–15`), but not enforced (no CI/hooks, R8c) |
| Module table: `service.py` = "all business logic — **validation**, …" | — | **Partly true now.** Before Task 07 there was no validation at all (W4). Now only `amount` is validated (`_parse_amount`). Category is a silent fallback, not validation. `date` and `month` are **not** validated (R3) |
| Module table: `cli.py` = "No business rules" | — | Still true: since Task 07 `cli.py` only maps `ValueError` → `Error:` + exit 1, which is presentation. The table does not mention that `main()` now returns an exit code |
| Test expectations: "Baseline: 7 passed, coverage 49% … do not make these numbers worse" | — | **Stale as a guard:** the floor is still the baseline, so dropping from 40 tests / 87% to 8 tests / 50% would not break the rule. It should ratchet to the latest `evidence/15` numbers |
| Architecture diagram | — | Leaves out the direct `service.py → models.py` import |

Other stale references (not in AGENTS.md):
- `ACCEPTANCE.md` AC2 says the category filter is "`service.py` line 43". It is now line 62 (`evidence/15`). Editing `ACCEPTANCE.md` needs approval, so it was not changed.
- The line numbers in `docs/05-risk-register.md` (e.g. `service.py:14-15`) refer to commit `1c45896`.

## 4. Readiness level: **2 — Documented**

**Not level 1:** the repo has more than a baseline:
- `AGENTS.md` (permissions, safe commands, prohibitions, gates) loaded through `CLAUDE.md`.
- `ACCEPTANCE.md` AC1–AC5.
- A baseline with raw evidence, and a risk register.
- A red → green process with evidence that was actually followed (Task 03, Task 07).

**Not level 3 (Agent-ready):** an agent cannot work safely without a human watching.
- Every gate is prose and nothing checks it automatically: no CI, hooks or permission settings.
- The environment cannot be rebuilt reproducibly: unpinned, undeclared dev tools, no Python version.
- `.gitignore` lets data-like files through (R8).
- The README is out of date with the code.
- The one data-loss risk (R4) is still open.

### Missing evidence needed for level 3

1. **Pinned, declared toolchain:** e.g. `requirements-dev.txt` and a declared Python version. Evidence: a
   fresh-venv install log where `pytest`, `ruff`, `mypy` and `pytest-cov` all run at the recorded versions (R6a).
2. **CI:** a workflow running `python -m pytest -v`, coverage, `ruff check .` and `mypy tracker` on push.
   Evidence: one green run and one deliberately red run (R8c).
3. **Enforced agent permissions:** a committed `.claude/settings.json` (or equivalent) allow/deny list that
   matches the AGENTS.md safe and forbidden commands. Evidence: a log of a denied forbidden command.
4. **Fresh-session proof:** a new session answering the rules question with the `@AGENTS.md` import, compared
   with one without it (R8d; `evidence/06` does not count).
5. **`.gitignore` hardening:** evidence is `git check-ignore -v demo.json report.txt my.json` → all ignored (R8).
6. **README re-verified:** every README command run with `--file` in a temp dir on the current code, including
   `list --month` and bare `pytest`, saved as evidence. The README updated for export formats, `--file`,
   amount rules and exit codes.
7. **AGENTS.md updated:** accurate validation wording, a ratcheted test/coverage floor, and the
   "stage by explicit path" rule.
8. **R4 mitigated** (atomic save + corrupted-file handling), with red/green evidence. Planned in
   `docs/08-background-agent.md`.
