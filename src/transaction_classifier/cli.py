import argparse
import csv
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from . import db, mapping, ml

console = Console()


def ingest(csv_path):
    """Reads CSV, predicts categories, overwrites CSV, and inserts unique transactions into DB."""
    db.init_db()

    try:
        rows = []
        fieldnames = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f, skipinitialspace=True)
            fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
            # Normalize rows to have stripped keys
            rows = []
            for row in reader:
                rows.append({k.strip(): v for k, v in row.items()})

        if not fieldnames:
            console.print("[red]Error: CSV file has no headers.[/red]")
            return

        # Get or create mapping
        header_mapping = mapping.get_mapping_for_headers(fieldnames)
        if not header_mapping:
            console.print(
                "[yellow]Unknown CSV format. Please map the columns:[/yellow]"
            )
            date_col = Prompt.ask(
                "Which column is the [bold]Date[/bold]?", choices=fieldnames
            )
            amount_col = Prompt.ask(
                "Which column is the [bold]Amount[/bold]?", choices=fieldnames
            )
            desc_col = Prompt.ask(
                "Which column is the [bold]Description[/bold]?", choices=fieldnames
            )

            header_mapping = {
                "date": date_col,
                "amount": amount_col,
                "description": desc_col,
            }
            mapping.save_mapping(fieldnames, header_mapping)
            console.print("[green]Mapping saved for future use.[/green]")

        if "predicted_category" not in fieldnames:
            fieldnames.append("predicted_category")

        added_to_db_count = 0
        for row in rows:
            # Use mapping to extract values
            raw_date = row.get(header_mapping["date"])
            raw_amount = row.get(header_mapping["amount"])
            raw_string = row.get(header_mapping["description"])

            if not raw_string:
                row["predicted_category"] = "Unknown"
                continue

            # Clean and Embed
            clean_string = ml.clean_text(raw_string)
            embedding = ml.get_embedding(clean_string)

            # Predict
            predicted_category, confidence = db.predict_category(embedding)
            if not predicted_category:
                predicted_category = "Unknown"
                confidence = 0.0

            row["predicted_category"] = predicted_category

            # Only insert if unique description
            if not db.transaction_exists_by_description(raw_string):
                date_obj = None
                if raw_date:
                    try:
                        date_obj = datetime.strptime(raw_date, "%Y-%m-%d").date()
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(raw_date, "%m/%d/%Y").date()
                        except ValueError:
                            pass

                db.insert_transaction(
                    date=date_obj,
                    amount=float(raw_amount) if raw_amount else 0.0,
                    raw_string=raw_string,
                    clean_string=clean_string,
                    predicted_category=predicted_category,
                    confidence_score=confidence,
                    embedding=embedding,
                )
                added_to_db_count += 1

        # Overwrite the original CSV
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        console.print(
            f"[green]Successfully processed {len(rows)} transactions.[/green]"
        )
        console.print(
            f"[green]CSV overwritten with predicted categories. Added {added_to_db_count} new unique transactions to DB.[/green]"
        )
    except FileNotFoundError:
        console.print(f"[red]Error: File not found {csv_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error during ingestion: {e}[/red]")


def category_manager(args):
    """Handles category management commands."""
    db.init_db()
    if args.category_command == "list":
        categories = db.get_all_categories()
        if not categories:
            console.print("[yellow]No categories defined.[/yellow]")
        else:
            table = Table(title="Defined Categories")
            table.add_column("Category Name", style="cyan")
            for cat in categories:
                table.add_row(cat)
            console.print(table)
    elif args.category_command == "add":
        try:
            db.add_category(args.name)
            console.print(f"[green]Added category: {args.name}[/green]")
        except Exception as e:
            console.print(f"[red]Error adding category: {e}[/red]")
    elif args.category_command == "rename":
        if db.rename_category(args.old, args.new):
            console.print(f"[green]Renamed {args.old} to {args.new}[/green]")
        else:
            console.print(f"[red]Category {args.old} not found.[/red]")
    elif args.category_command == "delete":
        if db.delete_category(args.name):
            console.print(
                f"[green]Deleted category {args.name}. Affected transactions reset to pending.[/green]"
            )
        else:
            console.print(f"[red]Category {args.name} not found.[/red]")


def review():
    """Human Review Loop."""
    db.init_db()
    pending = db.get_pending_transactions()
    if not pending:
        console.print("[yellow]No pending transactions to review.[/yellow]")
        return

    total = len(pending)
    idx = 0
    while idx < total:
        tx = pending[idx]
        categories = db.get_all_categories()
        console.clear()

        # Display Transaction info
        table = Table(title=f"Transaction Review [{idx+1}/{total}]")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Date", str(tx.date))
        table.add_row("Amount", f"${tx.amount:.2f}")
        table.add_row("Raw String", tx.raw_string)
        table.add_row("Clean String", tx.clean_string)
        console.print(table)

        # Display Categories
        if categories:
            console.print(f"Existing Categories: [cyan]{', '.join(categories)}[/cyan]")

        # Display Prediction
        confidence_pct = int(tx.confidence_score * 100)
        prediction_text = f"Prediction: [bold green]{tx.predicted_category}[/bold green] (Confidence: {confidence_pct}%)"
        console.print(Panel(prediction_text))

        # Prompt for input
        prompt_text = "Press [Enter] to accept, or type a category name"
        user_input = Prompt.ask(prompt_text, default=tx.predicted_category).strip()

        category = user_input if user_input else tx.predicted_category

        # Enforce category existence
        if category not in categories:
            confirm = Prompt.ask(
                f"Category [bold]{category}[/bold] does not exist. Create it?",
                choices=["y", "n"],
                default="y",
            )
            if confirm == "y":
                db.add_category(category)
            else:
                continue  # Re-prompt for the same transaction

        # Update DB
        db.update_transaction(tx.id, category)
        idx += 1

    console.print("[green]Review completed![/green]")


def main():
    parser = argparse.ArgumentParser(description="Transaction Classifier CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest transactions from a CSV file"
    )
    ingest_parser.add_argument("csv_path", help="Path to the CSV file")

    # Review command
    subparsers.add_parser("review", help="Review pending transactions")

    # Category command
    cat_parser = subparsers.add_parser("category", help="Manage categories")
    cat_sub = cat_parser.add_subparsers(
        dest="category_command", help="Category actions"
    )
    cat_sub.add_parser("list", help="List categories")
    add_p = cat_sub.add_parser("add", help="Add category")
    add_p.add_argument("name", help="Category name")
    ren_p = cat_sub.add_parser("rename", help="Rename category")
    ren_p.add_argument("old", help="Old name")
    ren_p.add_argument("new", help="New name")
    del_p = cat_sub.add_parser("delete", help="Delete category")
    del_p.add_argument("name", help="Category name")

    # Init DB command (optional but useful)
    subparsers.add_parser("init-db", help="Initialize the database")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest(args.csv_path)
    elif args.command == "review":
        review()
    elif args.command == "category":
        category_manager(args)
    elif args.command == "init-db":
        db.init_db()
        console.print("[green]Database initialized.[/green]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
