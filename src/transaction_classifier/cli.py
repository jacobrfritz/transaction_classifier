import argparse
import csv
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from . import db, ml

console = Console()


def ingest(csv_path):
    """Reads CSV, cleans, embeds, predicts, and inserts into DB."""
    db.init_db()

    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Expecting columns: date, amount, description
                # Adjusting based on common CSV headers if necessary
                raw_date = row.get("date") or row.get("Date")
                raw_amount = row.get("amount") or row.get("Amount")
                raw_string = (
                    row.get("description")
                    or row.get("Description")
                    or row.get("raw_string")
                )

                if not raw_string:
                    continue

                # Clean and Embed
                clean_string = ml.clean_text(raw_string)
                embedding = ml.get_embedding(clean_string)

                # Predict
                predicted_category, confidence = db.predict_category(embedding)
                if not predicted_category:
                    predicted_category = "Unknown"
                    confidence = 0.0

                # Insert
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
                count += 1

            console.print(f"[green]Successfully ingested {count} transactions.[/green]")
    except FileNotFoundError:
        console.print(f"[red]Error: File not found {csv_path}[/red]")
    except Exception as e:
        console.print(f"[red]Error during ingestion: {e}[/red]")


def review():
    """Human Review Loop."""
    pending = db.get_pending_transactions()
    if not pending:
        console.print("[yellow]No pending transactions to review.[/yellow]")
        return

    total = len(pending)
    for idx, tx in enumerate(pending, 1):
        console.clear()

        # Display Transaction info
        table = Table(title=f"Transaction Review [{idx}/{total}]")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Date", str(tx.date))
        table.add_row("Amount", f"${tx.amount:.2f}")
        table.add_row("Raw String", tx.raw_string)
        table.add_row("Clean String", tx.clean_string)

        console.print(table)

        # Display Prediction
        confidence_pct = int(tx.confidence_score * 100)
        prediction_text = f"Prediction: [bold green]{tx.predicted_category}[/bold green] (Confidence: {confidence_pct}%)"
        console.print(Panel(prediction_text))

        # Prompt for input
        prompt_text = "Press [Enter] to accept, or type the correct category"
        user_input = Prompt.ask(prompt_text, default=tx.predicted_category)

        # Update DB
        category = user_input if user_input else tx.predicted_category
        db.update_transaction(tx.id, category)

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

    # Init DB command (optional but useful)
    subparsers.add_parser("init-db", help="Initialize the database")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest(args.csv_path)
    elif args.command == "review":
        review()
    elif args.command == "init-db":
        db.init_db()
        console.print("[green]Database initialized.[/green]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
