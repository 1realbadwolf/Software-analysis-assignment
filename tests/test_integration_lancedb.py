"""Real filter-compiler and LanceDB integration; no paid model or GPU required."""
import lancedb
import pytest
from rag_system.retrieval.filters import compile_filters, combine

@pytest.fixture
def table(tmp_path):
    database = lancedb.connect(str(tmp_path / "lancedb"))
    rows = [
        {"document_id": "report.pdf", "chunk_index": 0, "text": "Report start"},
        {"document_id": "report.pdf", "chunk_index": 1, "text": "Report middle"},
        {"document_id": "report.pdf", "chunk_index": 2, "text": "Report end"},
        {"document_id": "notes.pdf", "chunk_index": 0, "text": "Notes"},
        {"document_id": "acquisition_agreement.pdf", "chunk_index": 0, "text": "Literal underscore"},
        {"document_id": "acquisitionXagreement.pdf", "chunk_index": 0, "text": "Near collision"},
        {"document_id": "100%_complete.pdf", "chunk_index": 0, "text": "Literal percent"},
        {"document_id": "100X_complete.pdf", "chunk_index": 0, "text": "Near percent"},
    ]
    result = database.create_table("documents", data=rows)
    yield result
    database.drop_table("documents")

def retrieve(table, spec):
    compiled = compile_filters(spec)
    return table.search().where(compiled.where).limit(100).to_list()

def test_eq_filter_selects_only_requested_document(table):
    rows = retrieve(table, {"document_id": {"eq": "report.pdf"}})
    assert len(rows) == 3
    assert {row["document_id"] for row in rows} == {"report.pdf"}

def test_in_filter_returns_union(table):
    rows = retrieve(table, {"document_id": {"in": ["report.pdf", "notes.pdf"]}})
    assert len(rows) == 4
    assert {row["document_id"] for row in rows} == {"report.pdf", "notes.pdf"}

def test_numeric_range_is_inclusive(table):
    rows = retrieve(table, {"document_id": "report.pdf", "chunk_index": {"gte": 1, "lte": 2}})
    assert sorted(row["chunk_index"] for row in rows) == [1, 2]

def test_contains_underscore_is_literal(table):
    rows = retrieve(table, {"document_name": {"contains": "acquisition_agreement"}})
    assert [row["document_id"] for row in rows] == ["acquisition_agreement.pdf"]

def test_contains_percent_is_literal(table):
    rows = retrieve(table, {"document_name": {"contains": "100%"}})
    assert [row["document_id"] for row in rows] == ["100%_complete.pdf"]

def test_combined_conditions_narrow_database_result(table):
    compiled = compile_filters({"chunk_index": {"gte": 1}})
    where = combine("document_id = 'report.pdf'", compiled)
    rows = table.search().where(where).limit(100).to_list()
    assert sorted((row["document_id"], row["chunk_index"]) for row in rows) == [
        ("report.pdf", 1), ("report.pdf", 2)
    ]

def test_no_match_returns_empty_result(table):
    assert retrieve(table, {"document_id": "missing.pdf"}) == []
