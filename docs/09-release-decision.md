# Task 09 — Release decision

**Decision date:** 2026-11-19 · **Reviewed version:** code commit `016cf32` (Task 07 R1/R2 fixes). It is pushed:
`origin/main` == local `main` == `156a527`. That commit adds only the Task 07 records (docs + `evidence/15`) on
top of `016cf32`, so the code is unchanged.
**Context:** single-user local CLI, personal finance data in one JSON file, public GitHub repo. "Release" means
the owner uses this version for real data and it is pushed to `origin`. There is no deployment.

## Decision: **CONDITIONAL**

### Definitions applied

- **GO:** critical checks pass and no unacceptable risks are left unresolved.
- **CONDITIONAL:** the known limitations have explicit controls and owners.
- **NO-GO:** serious risks or critical gaps in verification.

## Supporting evidence

**1. Critical checks pass** (`evidence/15_final_checks.txt`, HEAD `016cf32`, Python 3.14.3 / win32):
- `python -m pytest -v`: **40 passed, 0 failed**.
- Coverage: **87%** (`cli.py` 64%, `service.py` 97%, `exporters/models/storage` 100%).
- `ruff check .`: 1 finding, the pre-existing style-only I001 in `models.py:1`.
- `mypy tracker`: Success.
- AC1–AC5 hold (`docs/07-mitigations.md`). AC2's `--category` filter is still only checked manually.

**2. Fixed this cycle:**
- R1: 6 → 2. Red/green in `evidence/11`, `evidence/12`.
- R2: 4 → 2. Red/green in `evidence/13`, `evidence/14`.

**3. Open Confirmed risks with score ≥ 4** (`docs/05-risk-register.md`):

| Risk | Score | Why it does not force NO-GO for this context |
|------|-------|-----------------------------------------------|
| R4 data file emptied or overwritten (export onto data path; crash during `save`) | **6** (2×3) | This is the serious one: total data loss, no backup. It is acceptable only with the manual control C1 below. Without C1 the decision is NO-GO |
| R8 data-like files not ignored by git → personal data pushed to a public repo | **6** (2×3) | Owner-controlled: every commit so far staged files by explicit path (the Task 07 commits listed exact files). Control C2 |
| R3 dates and `--month` not validated → wrong monthly summaries | 4 | Wrong numbers, but data is recoverable and the symptom is visible. Control C3 |
| R5a CSV export without quoting → broken report | 4 | Only the export is affected, not the data file. Control C4 |
| R7 CLI wiring loosely tested (`cli.py` 64%) | 4 | The core logic is covered at 97–100%. Control C5 |
| R8c gates are prose only, no CI | 4 | Gates were followed and evidenced manually. Control C6 |

**4. Readiness level 2 — Documented** (`docs/06-readiness-audit.md`). The process is documented and was
followed, but nothing enforces it (no CI, no pinned toolchain, permissions in prose only). That is one more
reason this is not a plain GO.

**5. Known verification gaps** (`docs/07-mitigations.md` § "Not executed"):
- only one interpreter and one OS;
- no CI;
- no spreadsheet check;
- no fresh-clone install;
- README commands not re-run on the current code.

None of these hides a known failure. They limit confidence, so each one is a condition below.

## Conditions

| # | Condition | Control | Owner | Deadline / trigger |
|---|-----------|---------|-------|--------------------|
| C0 | Candidate actually released | **Done 2026-11-19.** Task 07 records committed (`156a527`). `git push origin main` → `9f701e1..156a527  main -> main`. After `git fetch`, `git rev-parse HEAD` and `git rev-parse origin/main` both print `156a52732ffacef469eb5f9062af512da277f29f`. The pushed code is `016cf32`, as tested in `evidence/15` (`156a527` changes docs/evidence only) | Almas (repo owner) | Done |
| C1 | R4 data loss | **Interim:** copy `expenses.json` to a dated backup before each session that adds or deletes; never pass a `.json` path, or the data file, to `export`. **Fix:** R4b atomic save + corrupted-file error, via `docs/08-background-agent.md`; R4a export guard as a separate task | Almas (repo owner) | Interim: from today. Fix: by 2026-12-03, **or before any second user or any non-owner data**, whichever comes first |
| C2 | R8 data in public repo | Stage by explicit path only and check `git diff --cached --name-only` before every commit (as done in Task 07); add `*.json` (except tracked ones), `demo*` and export `*.txt` to `.gitignore`; add the rule to AGENTS.md | Almas (.gitignore) + agent rule (AGENTS.md) | Before the next commit that adds any non-code file; `.gitignore` change by 2026-11-26 |
| C3 | R3 date / month | Until fixed: always use `--date YYYY-MM-DD` and `--month YYYY-MM` with two-digit months, and check `list` before trusting `summary` | Almas (repo owner) | Fix (validation + tests) by 2026-12-10, or before relying on monthly summaries for any decision |
| C4 | R5a CSV | Use `export json` for analysis; avoid commas in descriptions until `csv.writer` is in place (an intentional update of `test_export_csv_exact_format`) | Almas (repo owner) | By 2026-12-10, or before sharing any CSV report |
| C5 | R7 / CLI coverage, README drift | Before each push, smoke-run `list`, `list --month`, `delete`, `summary` and `export csv/json/txt` with `--file` in a temp dir and save the output as evidence; update the README (formats, `--file`, amount rules, exit codes) | Almas (repo owner) | README update by 2026-11-26; smoke run before every push |
| C6 | R8c no CI / R6a unpinned toolchain | Until CI exists: run the `evidence/15` commands manually before every push and keep the log. Add `requirements-dev.txt` pinned to the `pip freeze` versions, plus a GitHub Actions workflow | Almas (repo owner) | Manual check: every push. CI + pins by 2026-12-03 |

## Triggers that turn this into NO-GO

- Any re-run of the `evidence/15` commands shows a failing test, a new ruff/mypy issue, or a broken AC.
- A data-loss incident with `expenses.json` (R4), or real data found in git history (R8).
- C1's fix deadline passes, or a second user is added, while R4 is still open.

## What would make it GO

R4 and R8 mitigated with red/green evidence; CI green on the release commit. At that point no open
Confirmed risk scores above 4, and every remaining risk has an owner.
