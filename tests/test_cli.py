import csv
from unittest.mock import MagicMock, patch

from transaction_classifier import cli


def test_ingest_no_headers(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("")
    
    with patch("transaction_classifier.cli.console") as mock_console:
        cli.ingest(str(csv_file))
        mock_console.print.assert_any_call("[red]Error: CSV file has no headers.[/red]")

@patch("transaction_classifier.db.init_db")
@patch("transaction_classifier.mapping.get_mapping_for_headers")
@patch("transaction_classifier.ml.clean_text")
@patch("transaction_classifier.ml.get_embedding")
@patch("transaction_classifier.db.predict_category")
@patch("transaction_classifier.db.transaction_exists_by_description")
@patch("transaction_classifier.db.insert_transaction")
def test_ingest_success(
    mock_insert,
    mock_exists,
    mock_predict,
    mock_embedding,
    mock_clean,
    mock_mapping,
    mock_init,
    tmp_path,
):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Date,Amount,Description\n2026-04-26,-10.00,Test TX")

    mock_mapping.return_value = {
        "date": "Date",
        "amount": "Amount",
        "description": "Description",
    }
    mock_clean.return_value = "test tx"
    mock_embedding.return_value = [0.1] * 384
    mock_predict.return_value = ("Groceries", 0.95)
    mock_exists.return_value = False
    
    cli.ingest(str(csv_file))
    
    # Check if CSV was updated
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row["predicted_category"] == "Groceries"
    
    mock_insert.assert_called_once()

@patch("transaction_classifier.db.get_all_categories")
def test_category_list(mock_get_cats):
    mock_get_cats.return_value = ["Cat1", "Cat2"]
    args = MagicMock()
    args.category_command = "list"
    
    with patch("transaction_classifier.cli.console") as mock_console:
        cli.category_manager(args)
        assert mock_console.print.called

@patch("transaction_classifier.db.add_category")
def test_category_add(mock_add):
    args = MagicMock()
    args.category_command = "add"
    args.name = "NewCat"
    
    cli.category_manager(args)
    mock_add.assert_called_once_with("NewCat")

@patch("transaction_classifier.db.rename_category")
def test_category_rename(mock_rename):
    args = MagicMock()
    args.category_command = "rename"
    args.old = "Old"
    args.new = "New"
    
    cli.category_manager(args)
    mock_rename.assert_called_once_with("Old", "New")

@patch("transaction_classifier.db.delete_category")
def test_category_delete(mock_rename):
    args = MagicMock()
    args.category_command = "delete"
    args.name = "Cat"
    
    cli.category_manager(args)
    mock_rename.assert_called_once_with("Cat")

@patch("transaction_classifier.db.get_pending_transactions")
@patch("transaction_classifier.db.get_all_categories")
@patch("transaction_classifier.cli.Prompt.ask")
@patch("transaction_classifier.db.update_transaction")
@patch("transaction_classifier.db.init_db")
def test_review(mock_init, mock_update, mock_ask, mock_get_cats, mock_get_pending):
    mock_tx = MagicMock()
    mock_tx.predicted_category = "Groceries"
    mock_tx.confidence_score = 0.9
    mock_tx.amount = 10.0
    mock_tx.date = "2026-04-26"
    mock_tx.raw_string = "raw"
    mock_tx.clean_string = "clean"
    
    mock_get_pending.return_value = [mock_tx]
    mock_get_cats.return_value = ["Groceries"]
    mock_ask.return_value = "" # Accept default
    
    cli.review()
    
    mock_update.assert_called_once()

@patch("subprocess.run")
def test_database_lifecycle(mock_run):
    with cli.database_lifecycle():
        pass
    
    # Check if docker compose up and down were called
    assert mock_run.call_count == 2
    mock_run.assert_any_call(["docker", "compose", "up", "-d", "--wait", "db"], check=True)
    mock_run.assert_any_call(["docker", "compose", "down"], check=False)
