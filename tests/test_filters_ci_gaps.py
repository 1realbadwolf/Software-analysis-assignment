"""Manual assertions for previously uncovered numeric compilation paths."""
import pytest
from rag_system.retrieval.filters import compile_filters, FilterError

def test_integer_in_list_has_exact_sql():
    compiled = compile_filters({"chunk_index": {"in": [0, 2147483647]}})
    assert compiled.where == "chunk_index IN (0, 2147483647)"

def test_integer_equality_has_exact_sql():
    compiled = compile_filters({"chunk_index": {"eq": -2147483648}})
    assert compiled.where == "chunk_index = -2147483648"

def test_numeric_in_list_rejects_boolean_with_field_details():
    with pytest.raises(FilterError, match=r"filters\.chunk_index\.in must be an integer, got bool\."):
        compile_filters({"chunk_index": {"in": [True]}})

def test_multiple_fields_and_operators_have_exact_canonical_sql():
    compiled = compile_filters({
        "chunk_index": {"lte": 4, "gte": 0},
        "document_id": {"eq": "report.pdf"},
    })
    assert compiled.where == "document_id = 'report.pdf' AND chunk_index >= 0 AND chunk_index <= 4"
