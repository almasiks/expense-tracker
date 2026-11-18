# Acceptance Criteria

These must remain true after every change (refactoring, mitigations, agent edits).
Each criterion is checked by the command in the "Verified by" column.

| ID | Criterion | Verified by |
|----|-----------|-------------|
| AC1 | An added expense is saved to the JSON file and is still there after the app restarts. | `test_data_is_saved`, manual: `add` then `list` |
| AC2 | `total` / `summary` equal the exact sum of the matching expenses; `--month YYYY-MM` and `--category` filters include only matching records. | Sums: `test_total`, `test_totals_by_category`. `--month` filter: `test_filter_by_month`. `--category` filter: **no automated test at baseline** — `service.py` line 43 is never executed (see `evidence/02_coverage.txt`); manual check only. |
| AC3 | An unknown category is stored as `other` (never rejected silently or saved as-is). | `test_unknown_category_becomes_other` |
| AC4 | `export csv|json|txt <path>` writes a file that contains every stored expense; an unknown format raises an error and writes nothing. | `tests/test_export.py` (csv, json, txt, unknown format) |
| AC5 | The full test suite passes: `python -m pytest` reports 0 failed. | `python -m pytest -v` |
