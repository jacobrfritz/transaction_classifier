from unittest.mock import MagicMock, patch

from transaction_classifier import db


@patch("transaction_classifier.db.SessionLocal")
def test_transaction_exists_by_description(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    # Simulate transaction found
    mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
    exists = db.transaction_exists_by_description("some description")
    assert exists is True

    # Simulate transaction not found
    mock_session.query.return_value.filter.return_value.first.return_value = None
    exists = db.transaction_exists_by_description("other description")
    assert exists is False


@patch("transaction_classifier.db.SessionLocal")
def test_add_category(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    db.add_category("Test Category")
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@patch("transaction_classifier.db.SessionLocal")
def test_get_all_categories(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    mock_cat1 = MagicMock()
    mock_cat1.name = "A"
    mock_cat2 = MagicMock()
    mock_cat2.name = "B"
    mock_session.query.return_value.order_by.return_value.all.return_value = [
        mock_cat1,
        mock_cat2,
    ]

    categories = db.get_all_categories()
    assert categories == ["A", "B"]


@patch("transaction_classifier.db.SessionLocal")
def test_predict_category(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    # Mock return value for session.execute
    mock_result = MagicMock()
    mock_result.fetchone.return_value = ("Groceries", 0.9)
    mock_session.execute.return_value = mock_result
    
    cat, conf = db.predict_category([0.1] * 384)
    assert cat == "Groceries"
    assert conf == 0.9


@patch("transaction_classifier.db.SessionLocal")
def test_update_transaction(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    mock_tx = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_tx
    
    success = db.update_transaction("some-id", "Groceries")
    assert success is True
    assert mock_tx.actual_category == "Groceries"
    assert mock_tx.status == "verified"
    mock_session.commit.assert_called_once()


@patch("transaction_classifier.db.SessionLocal")
def test_insert_transaction(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    db.insert_transaction(
        date="2026-04-26",
        amount=10.0,
        raw_string="raw",
        clean_string="clean",
        predicted_category="Groceries",
        confidence_score=0.9,
        embedding=[0.1] * 384
    )
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@patch("transaction_classifier.db.SessionLocal")
def test_rename_category(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    mock_cat = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_cat
    
    success = db.rename_category("Old", "New")
    assert success is True
    assert mock_cat.name == "New"
    mock_session.commit.assert_called_once()


@patch("transaction_classifier.db.engine")
@patch("transaction_classifier.db.Base")
@patch("transaction_classifier.db.seed_categories")
def test_init_db(mock_seed, mock_base, mock_engine):
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    
    db.init_db()
    
    assert mock_conn.execute.called
    assert mock_base.metadata.create_all.called
    assert mock_seed.called


@patch("transaction_classifier.db.SessionLocal")
def test_seed_categories(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    # Case 1: Table is empty
    mock_session.query.return_value.count.return_value = 0
    db.seed_categories()
    assert mock_session.add.called
    assert mock_session.commit.called
    
    # Case 2: Table is not empty
    mock_session.reset_mock()
    mock_session.query.return_value.count.return_value = 5
    db.seed_categories()
    assert not mock_session.add.called


@patch("transaction_classifier.db.SessionLocal")
def test_get_transactions(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    mock_tx = MagicMock()
    mock_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_tx]
    mock_session.query.return_value.filter.return_value.filter.return_value.count.return_value = 1
    
    results, total = db.get_transactions(search="test", status="pending")
    assert results == [mock_tx]
    assert total == 1


@patch("transaction_classifier.db.SessionLocal")
def test_update_transactions_bulk(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    success = db.update_transactions_bulk(["id1", "id2"], "Dining")
    assert success is True
    mock_session.query.return_value.filter.return_value.update.assert_called_once()
    mock_session.commit.assert_called_once()


@patch("transaction_classifier.db.SessionLocal")
def test_get_category_stats(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    mock_session.query.return_value.group_by.return_value.all.return_value = [("Dining", 5)]
    mock_session.query.return_value.count.return_value = 5
    
    stats = db.get_category_stats()
    assert stats["total"] == 5
    assert stats["breakdown"][0]["category"] == "Dining"
    assert stats["breakdown"][0]["count"] == 5
