import argparse

from tracker.service import ExpenseService, CATEGORIES
from tracker.storage import JsonStorage


def build_parser():
    parser = argparse.ArgumentParser(prog="tracker", description="Simple expense tracker")
    parser.add_argument("--file", default="expenses.json", help="data file")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add", help="add an expense")
    add.add_argument("amount")
    add.add_argument("category", help="one of: " + ", ".join(CATEGORIES))
    add.add_argument("-d", "--description", default="")
    add.add_argument("--date", default=None, help="YYYY-MM-DD")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("--category")
    ls.add_argument("--month", help="YYYY-MM")

    rm = sub.add_parser("delete", help="delete an expense")
    rm.add_argument("id", type=int)

    summary = sub.add_parser("summary", help="totals by category")
    summary.add_argument("--month", help="YYYY-MM")

    exp = sub.add_parser("export", help="export expenses")
    exp.add_argument("format", help="csv, json or txt")
    exp.add_argument("path")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    service = ExpenseService(JsonStorage(args.file))

    if args.command == "add":
        e = service.add_expense(args.amount, args.category, args.description, args.date)
        print(f"Added #{e.id}: {e.amount:.2f} ({e.category})")
    elif args.command == "list":
        items = service.list_expenses(args.category, args.month)
        if not items:
            print("No expenses found.")
        for e in items:
            print(f"#{e.id:<3} {e.date}  {e.category:<14} {e.amount:>10.2f}  {e.description}")
    elif args.command == "delete":
        if service.delete_expense(args.id):
            print(f"Deleted #{args.id}")
        else:
            print(f"Expense #{args.id} not found")
    elif args.command == "summary":
        totals = service.totals_by_category(args.month)
        for cat, value in sorted(totals.items()):
            print(f"{cat:<14} {value:>10.2f}")
        print(f"{'TOTAL':<14} {service.total(month=args.month):>10.2f}")
    elif args.command == "export":
        service.export(args.format, args.path)
        print(f"Exported to {args.path}")
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
