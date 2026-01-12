#!/usr/bin/env python3
"""
To-Do CRUD App (single file, terminal)

Quick shortcuts:
  python todo.py add "Title" "Short description" [--due YYYY-MM-DD]
  python todo.py list [--sort] [--open]
  python todo.py done <id>
  python todo.py reopen <id>
  python todo.py update <id> [--title "..."] [--desc "..."] [--due YYYY-MM-DD | --clear-due]
  python todo.py delete <id>

Interactive menu:
  python todo.py
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, List

DATA_FILE = "todos.json"
DATE_FMT = "%Y-%m-%d"


@dataclass
class Todo:
    id: int
    title: str
    description: str
    due_date: Optional[str] = None  # "YYYY-MM-DD" or None
    completed: bool = False
    created_at: str = ""

    def due_as_date(self) -> Optional[date]:
        if not self.due_date:
            return None
        try:
            return datetime.strptime(self.due_date, DATE_FMT).date()
        except ValueError:
            return None


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load_todos() -> List[Todo]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Todo(**item) for item in raw]
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        print("Warning: Could not read todos.json. Starting with an empty list.")
        return []


def save_todos(todos: List[Todo]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in todos], f, indent=2)


def next_id(todos: List[Todo]) -> int:
    return max((t.id for t in todos), default=0) + 1


def parse_due_date(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    datetime.strptime(s, DATE_FMT)  # raises ValueError if invalid
    return s


def find_by_id(todos: List[Todo], todo_id: int) -> Optional[Todo]:
    for t in todos:
        if t.id == todo_id:
            return t
    return None


def print_todo(t: Todo) -> None:
    status = "✓" if t.completed else " "
    due = t.due_date if t.due_date else "-"
    print(f"[{status}] #{t.id} | {t.title} | Due: {due}")
    print(f"     {t.description}")
    print(f"     Created: {t.created_at}")


def list_todos(todos: List[Todo], sort_by_due: bool = False, open_only: bool = False) -> None:
    if not todos:
        print("No to-dos yet.")
        return

    items = todos[:]
    if open_only:
        items = [t for t in items if not t.completed]

    if sort_by_due:
        def key(t: Todo):
            d = t.due_as_date()
            return (0, d, t.id) if d else (1, date.max, t.id)
        items.sort(key=key)
    else:
        items.sort(key=lambda x: x.id)

    for t in items:
        print_todo(t)


# ---------- CRUD operations ----------

def add_todo(todos: List[Todo], title: str, description: str, due: Optional[str]) -> Todo:
    t = Todo(
        id=next_id(todos),
        title=title.strip(),
        description=description.strip(),
        due_date=due,
        completed=False,
        created_at=now_str(),
    )
    todos.append(t)
    save_todos(todos)
    return t


def update_todo_fields(todos: List[Todo], todo_id: int,
                       title: Optional[str], desc: Optional[str],
                       due: Optional[str], clear_due: bool) -> None:
    t = find_by_id(todos, todo_id)
    if not t:
        raise ValueError("To-do not found.")

    if title is not None:
        t.title = title.strip()
    if desc is not None:
        t.description = desc.strip()
    if clear_due:
        t.due_date = None
    elif due is not None:
        t.due_date = due

    save_todos(todos)


def set_complete(todos: List[Todo], todo_id: int, completed: bool) -> None:
    t = find_by_id(todos, todo_id)
    if not t:
        raise ValueError("To-do not found.")
    t.completed = completed
    save_todos(todos)


def delete_todo(todos: List[Todo], todo_id: int) -> None:
    t = find_by_id(todos, todo_id)
    if not t:
        raise ValueError("To-do not found.")
    todos.remove(t)
    save_todos(todos)


# ---------- Interactive menu (optional) ----------

def prompt_non_empty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Please enter a value (cannot be empty).")


def interactive_menu() -> None:
    todos = load_todos()

    while True:
        print("==== To-Do App ====")
        print("1) Add to-do")
        print("2) List to-dos")
        print("3) List to-dos (sorted by due date)")
        print("4) List open to-dos (sorted by due date)")
        print("5) Update to-do")
        print("6) Mark complete")
        print("7) Reopen")
        print("8) Delete")
        print("9) Exit")
        choice = input("Choose: ").strip()

        try:
            if choice == "1":
                title = prompt_non_empty("Title: ")
                desc = prompt_non_empty("Description: ")
                due_input = input("Due date (YYYY-MM-DD) (optional): ").strip()
                due = None
                if due_input:
                    try:
                        due = parse_due_date(due_input)
                    except ValueError:
                        print("Invalid date format. Skipping due date.")
                t = add_todo(todos, title, desc, due)
                print(f"Added #{t.id}.\n")

            elif choice == "2":
                list_todos(todos, sort_by_due=False, open_only=False)
                print()

            elif choice == "3":
                list_todos(todos, sort_by_due=True, open_only=False)
                print()

            elif choice == "4":
                list_todos(todos, sort_by_due=True, open_only=True)
                print()

            elif choice == "5":
                todo_id = int(input("ID: ").strip())
                t = find_by_id(todos, todo_id)
                if not t:
                    print("Not found.\n")
                    continue

                print("\nCurrent:")
                print_todo(t)
                print("\nLeave blank to keep unchanged. Use '-' to clear due date.")

                new_title = input("New title: ").strip()
                new_desc = input("New description: ").strip()
                new_due = input("New due date (YYYY-MM-DD) (Optional): ").strip()

                clear_due = (new_due == "-")
                due_val = None
                if new_due and not clear_due:
                    try:
                        due_val = parse_due_date(new_due)
                    except ValueError:
                        print("Invalid due date; not changing it.")
                        due_val = None
                        new_due = ""

                update_todo_fields(
                    todos,
                    todo_id,
                    title=new_title if new_title else None,
                    desc=new_desc if new_desc else None,
                    due=due_val if new_due else None,
                    clear_due=clear_due,
                )
                print("Updated.\n")

            elif choice == "6":
                todo_id = int(input("ID: ").strip())
                set_complete(todos, todo_id, True)
                print("Marked complete.\n")

            elif choice == "7":
                todo_id = int(input("ID: ").strip())
                set_complete(todos, todo_id, False)
                print("Reopened.\n")

            elif choice == "8":
                todo_id = int(input("ID: ").strip())
                delete_todo(todos, todo_id)
                print("Deleted.\n")

            elif choice == "9":
                print("Bye!")
                return

            else:
                print("Invalid choice.\n")

            # reload in case file was changed externally
            todos = load_todos()

        except ValueError as e:
            print(f"Error: {e}\n")


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Simple To-Do CRUD app (single file).")

    sub = p.add_subparsers(dest="cmd")

    add = sub.add_parser("add", help="Add a to-do quickly")
    add.add_argument("title", help="Title")
    add.add_argument("description", help="Short description")
    add.add_argument("--due", help="Due date YYYY-MM-DD (Optional)", default=None)

    ls = sub.add_parser("list", help="List to-dos")
    ls.add_argument("--sort", action="store_true", help="Sort by due date")
    ls.add_argument("--open", action="store_true", help="Show only incomplete items")

    done = sub.add_parser("done", help="Mark complete")
    done.add_argument("id", type=int)

    reopen = sub.add_parser("reopen", help="Mark incomplete")
    reopen.add_argument("id", type=int)

    upd = sub.add_parser("update", help="Update fields on a to-do")
    upd.add_argument("id", type=int)
    upd.add_argument("--title", help="New title")
    upd.add_argument("--desc", help="New description")
    upd.add_argument("--due", help="New due date YYYY-MM-DD (Optional)")
    upd.add_argument("--clear-due", action="store_true", help="Clear due date")

    rm = sub.add_parser("delete", help="Delete a to-do")
    rm.add_argument("id", type=int)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # No command => interactive menu
    if not args.cmd:
        interactive_menu()
        return

    todos = load_todos()

    try:
        if args.cmd == "add":
            due = None
            if args.due is not None:
                due = parse_due_date(args.due)  # may raise ValueError
            t = add_todo(todos, args.title, args.description, due)
            print(f"Added to-do #{t.id}: {t.title}")

        elif args.cmd == "list":
            list_todos(todos, sort_by_due=args.sort, open_only=args.open)

        elif args.cmd == "done":
            set_complete(todos, args.id, True)
            print(f"Marked #{args.id} complete.")

        elif args.cmd == "reopen":
            set_complete(todos, args.id, False)
            print(f"Reopened #{args.id}.")

        elif args.cmd == "update":
            due_val = None
            if args.due is not None:
                due_val = parse_due_date(args.due)  # may raise ValueError
            update_todo_fields(
                todos,
                args.id,
                title=args.title,
                desc=args.desc,
                due=due_val if args.due is not None else None,
                clear_due=args.clear_due,
            )
            print(f"Updated #{args.id}.")

        elif args.cmd == "delete":
            delete_todo(todos, args.id)
            print(f"Deleted #{args.id}.")

        else:
            parser.print_help()

    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
