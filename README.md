# Expense Tracker

A small command-line app for tracking personal expenses. Data is stored in a local JSON file.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python -m tracker.cli add 1500 food -d "lunch"
python -m tracker.cli add 300 transport --date 2026-11-02
python -m tracker.cli list
python -m tracker.cli list --month 2026-11
python -m tracker.cli summary
python -m tracker.cli delete 1
python -m tracker.cli export csv report.csv
```

Categories: food, transport, rent, entertainment, other.

## Tests

```bash
pytest
```
