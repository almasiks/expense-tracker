# Task 08 — Background agent task design (hypothetical)

This is a design only. No background agent was run, and no paid service is assumed. Any agent that can work in
a local git worktree and stop when told to fits (e.g. Claude Code started in the worktree, headless).

## 1. Task

**Mitigate R4b (part of R4): atomic save + corrupted-file handling.**
Source: `docs/05-risk-register.md` row R4, `evidence/10` § "R4b crash during save()" (0-byte file after a
simulated interrupt) and § "R4a" (`JSONDecodeError` on every later command).

Goal:
1. `JsonStorage.save` writes to a temporary file in the same directory and swaps it in with `os.replace`, so an
   exception during `json.dump` leaves the original file byte-for-byte unchanged.
2. `JsonStorage.load` raises a clear error (e.g. a `StorageError(ValueError)` with the path) on unreadable
   JSON, instead of a raw `JSONDecodeError`.
3. `cli.py` prints `Error: …` to stderr and returns exit code 1 for that error. This is the same pattern as R2
   in `docs/07-mitigations.md`.

**Out of scope** (each needs its own task):
- The R4a export-path guard (`exporters.py`/`service.py`).
- Backups.
- Repairing already-corrupted files.

## 2. Isolation: branch + worktree

The human sets this up; the agent never touches the main checkout.

```bash
cd "<repo>"                                   # main checkout, clean (git status shows nothing)
git status --short                            # must print nothing
git worktree add -b agent/r4-atomic-save ../expense-tracker-r4 main
git worktree list                             # shows the new worktree on agent/r4-atomic-save
```

The agent works **only** in `../expense-tracker-r4`. It reuses the main checkout's venv by absolute path, so no
`pip install` is needed:

```bash
cd ../expense-tracker-r4
PY="<repo>/.venv/Scripts/python"              # macOS/Linux: <repo>/.venv/bin/python
"$PY" -c "import tracker, os; print(os.path.abspath(tracker.__file__))"
# must print a path inside expense-tracker-r4 (no editable install exists, so the cwd wins); otherwise stop
```

## 3. Allowed files (allowlist)

| File | Allowed change |
|------|----------------|
| `tracker/storage.py` | atomic `save`, clear error in `load` |
| `tracker/cli.py` | **only** catching the new storage error in `main()` → `Error: …`, `return 1` |
| `tests/test_storage.py` (new) | new tests |
| `tests/test_cli.py` | **add** tests only; existing tests unchanged |
| `evidence/16_R4_red.txt`, `evidence/17_R4_green.txt`, `evidence/18_R4_agent_checks.txt` (new) | raw command output |
| `docs/10-agent-run-R4.md` (new) | the agent's report (see §6) |

Any other path in `git diff --name-only main` or `git status --short` makes the run **out of scope** (§8).
Explicitly off-limits:
- `tracker/service.py`, `tracker/exporters.py`, `tracker/models.py`
- existing tests in `tests/test_service.py` / `tests/test_export.py`
- `requirements.txt`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `ACCEPTANCE.md`, `README.md`, `docs/0*.md`

## 4. Allowed commands

All of them run inside the worktree only:
- The AGENTS.md "Safe commands" with `"$PY" -m` in place of `python -m`:
  `"$PY" -m pytest -v`, `"$PY" -m pytest --cov=tracker --cov-report=term-missing`, `"$PY" -m ruff check .`
  (no `--fix`), `"$PY" -m mypy tracker`.
- The CLI only with `--file` pointing into a temp directory created by the agent; the agent deletes it at the end.
- Read-only git: `git status`, `git diff`, `git diff main --stat`, `git diff --name-only main`, `git log`.
- File reads/edits on allowlisted paths (§3).
- Redirecting command output into the allowlisted `evidence/` files.

## 5. Limits

| Limit | Value | On breach |
|-------|-------|-----------|
| Wall-clock time | 45 minutes | stop → §8 "timeout" |
| Red → green iterations (an edit plus a full-suite run) | max 5 | stop → §8 "tests still failing" |
| Full-suite runs | max 10 | stop |
| Diff size (`git diff main --stat`) | ≤ ~200 changed lines, ≤ 7 files | stop and report; likely scope creep |
| Network | none | — |

## 6. Prohibited operations

Everything in AGENTS.md § "Forbidden" and § "Needs human approval first" applies unchanged. In particular:
- no `pip install` or `requirements.txt` changes;
- no writing to a real `expenses.json`;
- no weakening, skipping or deleting tests;
- no fabricated or edited tool output.

Extra rules for the background run:
- **No `git commit`, `git push`, `git merge`, `git rebase`, `git reset`, `git checkout`/`switch` of another
  branch, `git worktree remove`, `git branch -D`.** The agent leaves its changes **uncommitted** in the worktree.
  The human commits after review, matching AGENTS.md "commit needs approval".
- No access to the main checkout or any path outside the worktree, except the venv interpreter (read/execute)
  and the agent's own temp directory.
- No deployment of any kind; no publishing anything (artifacts, gists, PRs).
- No `git add .` / `git add -A` (R8). The agent does not stage files at all.

## 7. Required output artifacts

The agent must produce these before it reports "done":

1. **Change summary:** `docs/10-agent-run-R4.md`. It covers what changed (file:function), why, the
   decisions made, and anything it could not do.
2. **Diff:** the output of `git diff main` and `git status --short`, both pasted into the report.
   New files also appear in `git status`.
3. **Test log:**
   - `evidence/16_R4_red.txt`: the new tests fail on the unchanged code. Required failures: original file
     changed after a monkeypatched `json.dump` raise; raw `JSONDecodeError` instead of the clear error;
     CLI exit code ≠ 1.
   - `evidence/17_R4_green.txt`: full suite, **0 failed**, with the exact counts.
4. **Build/lint/type result:** `evidence/18_R4_agent_checks.txt`, holding coverage, `ruff check .` and
   `mypy tracker`. Compared with `evidence/15`: 40 tests → more, coverage ≥ 87%, ruff ≤ 1 finding, mypy clean.
   Build = n/a (pure Python).
5. **Risk notes:** a section in the report covering:
   - the new L×I for R4b and the residual risk (R4a export guard still open; behavior on network/OneDrive
     folders where `os.replace` may fail if the file is locked — Windows);
   - any new risk introduced (e.g. leftover temp files).
6. **AC1–AC5 re-check**, as in `docs/07-mitigations.md`.

## 8. Failure handling and rollback

| Situation | Agent action | Human action |
|-----------|--------------|--------------|
| Tests still failing after 5 iterations | Stop editing. Write the report with status **FAILED**, the last full pytest output and the hypothesis. Do **not** weaken tests | Read the report; either give a narrower follow-up task or discard (below) |
| Timeout (45 min) | Stop at once. Report status **TIMEOUT** with the current diff and last test output | Same as above |
| Out-of-scope edit (path not in §3, or a forbidden command attempted) | Report it; do not try to "undo" by rewriting history | Treat the **whole run as rejected** — discard, do not cherry-pick parts |
| Existing test changed or deleted | — (forbidden) | Reject the run |
| Green, all artifacts present | Report status **DONE** and stop | Review gate (§9) |

**Discard a run** (human only; it deletes uncommitted work in the worktree, which is the intent):

```bash
cd "<repo>"
git worktree remove --force ../expense-tracker-r4
git branch -D agent/r4-atomic-save          # deleting a branch needs approval per AGENTS.md
git worktree prune
```

`main` is never touched by the agent, so discarding needs no revert.

**Rollback after a merge:** `git revert <merge-or-commit-sha>` on `main`, then the AGENTS.md gates again
(full suite 0 failed, show diff). Never `git reset --hard` or a force-push; both are forbidden.

## 9. Human review and approval gate (before merge)

There is no deployment step. "Release" means merging to `main` and, with separate approval, pushing.

1. **Scope:** `git -C ../expense-tracker-r4 diff --name-only main` and `git status --short` show allowlisted
   paths only.
2. **Read the diff in full.** Existing tests are unchanged:
   `git diff main -- tests/test_service.py tests/test_export.py` is empty, and `tests/test_cli.py` has only
   additions.
3. **Evidence:** red shows the intended failures; green shows 0 failed. The human **re-runs**
   `python -m pytest -v`, `ruff check .` and `mypy tracker` in the worktree themselves rather than trusting the
   agent's evidence (R8c: no CI yet).
4. **AC1–AC5** still hold, and no numbers are worse than `evidence/15`.
5. **Approve.** Then the human commits in the worktree, staging by explicit path, with the message
   `Task 10: mitigate R4b atomic save`.
6. **Merge:** `git switch main` and `git merge --no-ff agent/r4-atomic-save`.
7. **Re-run** the full suite on `main`.
8. **Push** only with separate approval.
9. **Clean up:** `git worktree remove ../expense-tracker-r4`, plus a branch deletion if approved.
10. **Records:** update the R4 row in `docs/05-risk-register.md`.
