import pytest

from rag_system.retrieval.filters import (
    FilterError,
    _check_int,
    _check_string,
)


def test_whitespace_only_string_is_rejected():
    with pytest.raises(FilterError):
        _check_string("document_id", "eq", "   ")

def test_document_name_contains_trims_surrounding_spaces():
    from rag_system.retrieval.filters import _like_pattern

    assert _like_pattern(" NDA ") == "'%NDA%'"

@pytest.mark.parametrize("value", [True, False])
def test_boolean_is_rejected_as_integer(value):
    with pytest.raises(FilterError):
        _check_int("page", "eq", value)

def test_non_string_operator_key_raises_filter_error():
    from rag_system.retrieval.filters import compile_filters

    with pytest.raises(FilterError):
        compile_filters({"document_id": {1: "test", "eq": "abc"}})

def test_unicode_control_character_is_rejected():
    with pytest.raises(FilterError):
        _check_string("document_id", "eq", "abc\u0085def")