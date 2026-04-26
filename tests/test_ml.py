from transaction_classifier import ml


def test_clean_text():
    raw = "TST* DOORDASH #9923 2026-03-12"
    cleaned = ml.clean_text(raw)
    assert "doordash" in cleaned
    assert "2026-03-12" not in cleaned
    assert "tst" not in cleaned
    assert "9923" not in cleaned


def test_clean_text_starbucks():
    raw = "STARBUCKS COFFEE #1234"
    cleaned = ml.clean_text(raw)
    assert cleaned == "starbucks coffee"


def test_get_embedding():
    text = "starbucks coffee"
    embedding = ml.get_embedding(text)
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)
