import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from uuid import uuid4
from transaction_classifier.app import app

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("transaction_classifier.app.db") as mock:
        yield mock

def test_list_categories(mock_db):
    mock_db.get_all_categories.return_value = ["Dining", "Groceries"]
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert response.json() == ["Dining", "Groceries"]

def test_add_category(mock_db):
    response = client.post("/api/categories", json={"name": "NewCat"})
    assert response.status_code == 200
    mock_db.add_category.assert_called_once_with("NewCat")

def test_get_transactions(mock_db):
    mock_tx = MagicMock()
    mock_tx.id = uuid4()
    mock_tx.date = "2023-01-01"
    mock_tx.amount = 10.50
    mock_tx.raw_string = "Test Tx"
    mock_tx.predicted_category = "Dining"
    mock_tx.confidence_score = 0.9
    mock_tx.actual_category = None
    mock_tx.status = "pending"
    
    mock_db.get_transactions.return_value = ([mock_tx], 1)
    
    response = client.get("/api/transactions?search=Test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["transactions"][0]["raw_string"] == "Test Tx"
    mock_db.get_transactions.assert_called_once()

def test_bulk_update_transactions(mock_db):
    tx_ids = [str(uuid4()), str(uuid4())]
    mock_db.update_transactions_bulk.return_value = True
    
    response = client.put("/api/transactions/bulk", json={
        "ids": tx_ids,
        "category": "Groceries"
    })
    
    assert response.status_code == 200
    mock_db.update_transactions_bulk.assert_called_once()

def test_upload_csv_mapping_required(mock_db):
    with patch("transaction_classifier.app.mapping") as mock_mapping:
        mock_mapping.get_mapping_for_headers.return_value = None
        
        csv_content = "Col1,Col2\nVal1,Val2"
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "mapping_required"

def test_upload_csv_with_mapping(mock_db):
    with patch("transaction_classifier.app.mapping") as mock_mapping:
        with patch("transaction_classifier.app.ml") as mock_ml:
            mock_ml.clean_text.return_value = "clean"
            mock_ml.get_embedding.return_value = [0.1] * 384
            mock_db.transaction_exists_by_description.return_value = False
            mock_db.predict_category.return_value = ("Dining", 0.95)
            
            csv_content = "MyDate,MyAmount,MyDesc\n2026-04-26,10.50,Lunch"
            response = client.post(
                "/api/upload",
                data={
                    "date_col": "MyDate",
                    "amount_col": "MyAmount",
                    "description_col": "MyDesc"
                },
                files={"file": ("test.csv", csv_content, "text/csv")}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_mapping.save_mapping.assert_called_once()
            mock_db.insert_transaction.assert_called_once()

def test_get_stats(mock_db):
    mock_db.get_category_stats.return_value = {
        "total": 10,
        "breakdown": [{"category": "Dining", "count": 5, "percentage": 50.0}]
    }
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json()["total"] == 10
