from unittest.mock import mock_open, patch

from transaction_classifier import mapping


def test_get_signature():
    headers = ["Date", "Amount", "Description"]
    sig = mapping._get_signature(headers)
    assert sig == "amount,date,description"


def test_get_mapping_for_headers_default():
    headers = ["Date", "Amount", "Description"]
    # Should match defaults
    m = mapping.get_mapping_for_headers(headers)
    assert m == {"date": "Date", "amount": "Amount", "description": "Description"}


def test_get_mapping_for_headers_aliases():
    headers = ["tx_date", "cost", "notes"]
    m = mapping.get_mapping_for_headers(headers)
    assert m == {"date": "tx_date", "amount": "cost", "description": "notes"}


def test_get_mapping_for_headers_not_found():
    headers = ["random", "cols"]
    m = mapping.get_mapping_for_headers(headers)
    assert m is None


@patch("os.path.exists")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"a,b,c": {"date": "a", "amount": "b", "description": "c"}}',
)
def test_load_mappings(mock_file, mock_exists):
    mock_exists.return_value = True
    mappings = mapping.load_mappings()
    assert "a,b,c" in mappings
    assert mappings["a,b,c"]["date"] == "a"


@patch("transaction_classifier.mapping.load_mappings")
@patch("builtins.open", new_callable=mock_open)
def test_save_mapping(mock_file, mock_load):
    mock_load.return_value = {}
    headers = ["X", "Y", "Z"]
    m = {"date": "X", "amount": "Y", "description": "Z"}
    mapping.save_mapping(headers, m)

    # Check that open was called to write
    mock_file.assert_called_once_with("csv_mappings.json", "w")
