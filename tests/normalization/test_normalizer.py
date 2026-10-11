from app.contracts import RawDocument, SourceType
from app.normalization.cleaners import clean_text, clean_unicode, clean_whitespace
from app.normalization.schemas import normalize_record_schema
from app.normalization.normalizer import normalize_document, compute_content_hash


def test_clean_unicode():
    raw = "Orbital\xa0Robotics\u200b with “smart quotes” and — em-dash"
    cleaned = clean_unicode(raw)
    assert "\xa0" not in cleaned
    assert "\u200b" not in cleaned
    assert '"smart quotes"' in cleaned
    assert "--" in cleaned


def test_clean_whitespace():
    raw = "Line 1   with   spaces\r\n\r\n\r\n\r\nLine 2\n\n\nLine 3"
    cleaned = clean_whitespace(raw)
    assert "   " not in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_schema_drift_aliases_and_unexpected_fields():
    raw_record = {
        "employee_id": 999,
        "emp_name": "Gordon Freeman",
        "dept": "Anomalous Materials",
        "clearance_level": "Level 4",
        "badge_color": "Blue",
    }
    canonical, extra, schema_hash = normalize_record_schema(raw_record)

    # Known aliases mapped to canonical names
    assert canonical["id"] == 999
    assert canonical["name"] == "Gordon Freeman"
    assert canonical["department"] == "Anomalous Materials"

    # Unexpected fields preserved in extra without crashing
    assert extra["clearance_level"] == "Level 4"
    assert extra["badge_color"] == "Blue"
    assert len(schema_hash) == 12


def test_normalize_document_deterministic_hash():
    raw_doc = RawDocument(
        source_id="src-test",
        source_type=SourceType.CSV,
        raw_content="name: Alice\nrole: Engineer",
        metadata={"source_file": "data/raw/csv/team.csv", "row_data": {"name": "Alice"}},
    )
    doc1 = normalize_document(raw_doc)
    doc2 = normalize_document(raw_doc)

    assert doc1.content_hash == doc2.content_hash
    assert doc1.source_name == "team.csv"
    assert doc1.title == "Team"
    assert doc1.metadata["canonical_fields"]["name"] == "Alice"
