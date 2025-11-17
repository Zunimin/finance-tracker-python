from importlib.metadata import requires
from typing import List, Dict, Optional
import os.path
from datetime import datetime
import json
import argparse

DATA_FILE = "expenses.json"

class Expense:
    def __init__(self, id: int, title: str, description: str, amount: float, date: str = None):
        self.id = id
        self.title = title
        self.description = description
        self.amount = amount
        self.date = date or datetime.now().strftime("%d-%m-%Y")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "amount": self.amount,
            "date": self.date
        }
    @classmethod
    def from_dict(cls, data: Dict) -> 'Expense':
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            amount=data["amount"],
            date=data["date"]
        )

class ExpenseTracker:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.expenses = self.load_expenses()

    def load_expenses(self) -> List[Expense]:
        if not os.path.exists(self.data_file):
            return []
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return [Expense.from_dict(expense_data) for expense_data in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def save_expenses(self) -> None:
        with open(self.data_file, 'w') as f:
            json_data = [expense.to_dict() for expense in self.expenses]
            json.dump(json_data, f, indent=2)

    def get_next_id(self) -> int:
        if not self.expenses:
            return 1
        return max(expense.id for expense in self.expenses) + 1

    def add_expense(self, title: str, description: str, amount: float) -> Expense:
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        expense = Expense(
            id=self.get_next_id(),
            title=title,
            description=description,
            amount=amount
        )

        self.expenses.append(expense)
        self.save_expenses()
        return expense

    def delete_expense(self, expense_id: int, ) -> bool:
        for i, expense in enumerate(self.expenses):
            if expense.id == expense_id:
                del self.expenses[i]
                self.save_expenses()
                return True

        return False

    def update_expense(self, expense_id: int, title:str = None, description: str = None, amount: float = None) -> bool:
        for expense in self.expenses:
            if expense.id == expense_id:
                if title is not None:
                    expense.title = title
                if description is not None:
                    expense.description = description
                if amount is not None:
                    if amount <= 0:
                        raise ValueError("Amount must be positive.")
                    expense.amount = amount
                self.save_expenses()
                return True

        return False

    def list_expenses(self):
        return self.expenses

    def get_total_expenses(self, month: Optional[int] = None) -> float:
        total = 0.0
        current_year = datetime.now().year

        for expense in self.expenses:
            expense_date = datetime.strptime(expense.date, "%d-%m-%Y")

            if month is None:
                total += expense.amount
            elif expense_date.month == month and expense_date == current_year:
                total += expense.amount

        return total

def format_currency(amount: float) -> str:
        return f"{amount:.2f}"

def print_expenses(expenses: List[Expense]) -> None:
    if not expenses:
        print("No expenses found.")
        return

    print(f"{'ID':<4} {'Date':<12} {'Description':<20} {'Amount':<10}")
    print("-" * 50)
    for expense in expenses:
        print(f"{expense.id:<4} {expense.date:<12} {expense.description:<20} {format_currency(expense.amount):<10}")

def main():
    tracker = ExpenseTracker()

    parser = argparse.ArgumentParser(description="Expense Tracker - Manage your finances")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("add", help="Add a new expense")
    add_parser.add_argument("--title", required=True, help="Title of the expense")
    add_parser.add_argument("--description", required=True, help="Description of the expense")
    add_parser.add_argument("--amount", type=float, required=True, help="Amount of the expense")

    delete_parser = subparsers.add_parser("delete", help="Delete an expense")
    delete_parser.add_argument("--id", type=int, required=True, help="ID of the expense to delete")

    update_parser = subparsers.add_parser("update", help="Update an expense")
    update_parser.add_argument("--id", type=int, required=True, help="id of an expense")
    update_parser.add_argument("--title", help="New title for the expense")
    update_parser.add_argument("--description", help="New description for the expense")
    update_parser.add_argument("--amount", type=float, help="New amount for the expense")

    subparsers.add_parser("list", help="List all expenses")

    summary_parser = subparsers.add_parser("summary", help="Show summary of expenses")
    summary_parser.add_argument("--month", type=int, help="Month number (1-12) for monthly summary")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "add":
            expense = tracker.add_expense(args.title, args.description, args.amount)
            print(f"Expense added successfully (ID: {expense.id})")

        elif args.command == "delete":
            if tracker.delete_expense(args.id):
                print("Expense deleted successfully")
            else:
                print(f"Error: Expense with ID {args.id} not found")

        elif args.command == "update":
            if args.title and not args.description and not args.amount:
                print("Error: Please provide either --description or --amount to update")
                return

            if tracker.update_expense(args.id, args.title, args.description, args.amount):
                print("Expense updated successfully")
            else:
                print(f"Error: Expense with ID {args.id} not found")

        elif args.command == "list":
            expenses = tracker.list_expenses()
            print_expenses(expenses)

        elif args.command == "summary":
            if args.month:
                if args.month < 1 or args.month > 12:
                    print("Error: Month must be between 1 and 12")
                    return

                total = tracker.get_total_expenses(month=args.month)
                month_name = datetime(2000, args.month, 1).strftime("%B")
                print(f"Total expenses for {month_name}: {format_currency(total)}")
            else:
                total = tracker.get_total_expenses()
                print(f"Total expenses: {format_currency(total)}")

        else:
            parser.print_help()

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
