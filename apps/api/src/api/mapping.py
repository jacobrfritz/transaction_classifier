import json
import logging
import os

MAPPINGS_FILE = "csv_mappings.json"

logger = logging.getLogger(__name__)


def _get_signature(headers: list[str]) -> str:
    """Returns a unique signature for a set of headers."""
    return ",".join(sorted([h.strip().lower() for h in headers]))


def load_mappings() -> dict[str, dict[str, str]]:
    """Loads mappings from the JSON file."""
    if not os.path.exists(MAPPINGS_FILE):
        return {}
    try:
        with open(MAPPINGS_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_mapping(headers: list[str], mapping: dict[str, str]) -> None:
    """Saves a new mapping configuration."""
    mappings = load_mappings()
    signature = _get_signature(headers)
    mappings[signature] = mapping
    with open(MAPPINGS_FILE, "w") as f:
        json.dump(mappings, f, indent=4)


def get_mapping_for_headers(headers: list[str]) -> dict[str, str] | None:
    """Returns a mapping for the given headers if one exists."""
    mappings = load_mappings()
    signature = _get_signature(headers)

    # Try exact match signature
    if signature in mappings:
        return mappings[signature]

    # Default common mappings if no custom mapping exists
    common_matches = {
        "date": ["date", "Date", "tx_date", "transaction_date"],
        "amount": ["amount", "Amount", "value", "cost", "price"],
        "description": [
            "description",
            "Description",
            "raw_string",
            "details",
            "memo",
            "notes",
        ],
    }

    potential_mapping = {}
    lower_headers = [h.lower() for h in headers]

    for key, aliases in common_matches.items():
        for alias in aliases:
            if alias.lower() in lower_headers:
                # Find the original header casing
                original_header = headers[lower_headers.index(alias.lower())]
                potential_mapping[key] = original_header
                break

    if len(potential_mapping) == 3:
        return potential_mapping

    return None
