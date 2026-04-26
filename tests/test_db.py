from unittest.mock import patch, MagicMock
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
