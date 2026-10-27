# tests/test_filters.py
import pytest
from unittest.mock import patch

from rag_system.retrieval.filters import (
    FilterError,
    CompiledFilter,
    _check_string,
    _check_int,
    _quote,
    _like_pattern,
    compile_filters,
    combine,
)


@pytest.fixture
def valid_filter():
    return {
        "document_id": {"eq": "07_nda.pdf"},
        "chunk_index": {"gte": 0, "lte": 4},
    }


class TestFilterError:
    def test_filter_error_is_value_error(self):
        assert issubclass(FilterError, ValueError)

    def test_filter_error_message(self):
        with pytest.raises(FilterError, match="must be a string"):
            _check_string("field", "eq", 123)


class TestCompiledFilter:
    def test_compiled_filter_creation(self):
        where = "document_id = '07_nda.pdf'"
        spec = {"document_id": "07_nda.pdf"}
        cf = CompiledFilter(where=where, spec=spec)
        assert cf.where == where
        assert cf.spec == spec

    def test_compiled_filter_signature(self):
        cf = CompiledFilter(where="a AND b", spec={"field": "value"})
        assert cf.signature == "a AND b"

    def test_compiled_filter_str(self):
        cf = CompiledFilter(where="a AND b", spec={"field": "value"})
        assert str(cf) == "a AND b"


class TestCheckString:
    def test_valid_string(self):
        result = _check_string("field", "eq", "test")
        assert result == "test"

    def test_empty_string_raises_error(self):
        with pytest.raises(FilterError, match="must not be empty"):
            _check_string("field", "eq", "")

    def test_too_long_string_raises_error(self):
        long_value = "a" * (_MAX_STRING_LENGTH + 1)
        with pytest.raises(FilterError, match="_MAX_STRING_LENGTH"):
            _check_string("field", "eq", long_value)

    def test_forbidden_quote_raises_error(self):
        with pytest.raises(FilterError, match="forbidden character"):
            _check_string("field", "eq", "test'")

    def test_forbidden_backslash_raises_error(self):
        with pytest.raises(FilterError, match="forbidden character"):
            _check_string("field", "eq", "test\\")

    def test_control_character_raises_error(self):
        with pytest.raises(FilterError, match="control character"):
            _check_string("field", "eq", "\x00")

    def test_wildcard_escaped_in_like_pattern(self):
        result = _like_pattern("test%value%")
        assert result == "'\\%%test\\%%value\\%%'"


class TestCheckInt:
    def test_valid_int(self):
        result = _check_int("field", "eq", 42)
        assert result == 42

    def test_bool_raises_error(self):
        with pytest.raises(FilterError, match="must be an integer"):
            _check_int("field", "eq", True)

    def test_out_of_range_min_raises_error(self):
        with pytest.raises(FilterError, match="int32 range"):
            _check_int("field", "eq", -(2**31))

    def test_out_of_range_max_raises_error(self):
        with pytest.raises(FilterError, match="int32 range"):
            _check_int("field", "eq", 2**31)


class TestCompileField:
    def test_eq_string_field(self):
        result = _compile_field(
            "document_id", "document_id", "string", ("eq",), "test"
        )
        assert result == ["document_id = 'test'"]

    def test_in_list_string_field(self):
        result = _compile_field(
            "document_id", "document_id", "string", ("in",), ["a", "b"]
        )
        assert result == ["document_id IN ('a', 'b')"]

    def test_contains_string_field(self):
        result = _compile_field(
            "document_name", "document_id", "string", ("contains",), "nda"
        )
        assert result[0] == "document_id LIKE '%\\%nda\\%%' ESCAPE '\\'"

    def test_int_comparison_operator(self):
        result = _compile_field(
            "chunk_index", "chunk_index", "int", ("gte",), 10
        )
        assert result == ["chunk_index >= 10"]

    def test_unknown_operator_raises_error(self):
        with pytest.raises(FilterError, match="does not support"):
            _compile_field(
                "document_id", "document_id", "string", ("eq",), {"not": "test"}
            )


class TestCompileFilters:
    def test_valid_filter_compiles(self):
        result = compile_filters(valid_filter)
        assert isinstance(result, CompiledFilter)
        assert "document_id" in result.where

    def test_none_filter_returns_none(self):
        result = compile_filters(None)
        assert result is None

    def test_empty_dict_raises_error(self):
        with pytest.raises(FilterError, match="is empty"):
            compile_filters({})

    def test_unknown_field_raises_error(self):
        with pytest.raises(FilterError, match="Unsupported filter field"):
            compile_filters({"unknown": {"eq": "test"}})

    def test_empty_filter_object_raises_error(self):
        with pytest.raises(FilterError, match="has no operators"):
            _compile_field("document_id", "document_id", "string", ("eq",), {})

    def test_in_list_empty_raises_error(self):
        with pytest.raises(FilterError, match="is an empty list"):
            _compile_field(
                "document_id", "document_id", "string", ("in",), []
            )

    def test_in_list_too_long_raises_error(self):
        long_list = [f"item{i}" for i in range(_MAX_IN_ITEMS + 1)]
        with pytest.raises(FilterError, match="_MAX_IN_ITEMS"):
            _compile_field(
                "document_id", "document_id", "string", ("in",), long_list
            )

    def test_compiled_filter_passes_through(self):
        cf = CompiledFilter(where="a AND b", spec={"field": "value"})
        result = compile_filters(cf)
        assert result is cf


class TestCombine:
    def test_combine_with_none_user_filter(self):
        where = "internal WHERE"
        compiled = None
        result = combine(where, compiled)
        assert result == "internal WHERE"

    def test_combine_with_none_internal_filter(self):
        where = None
        compiled = CompiledFilter(where="user WHERE", spec={})
        result = combine(where, compiled)
        assert result == "user WHERE"

    def test_combine_both_filters(self):
        internal_where = "internal WHERE"
        user_where = "user WHERE"
        compiled = CompiledFilter(where=user_where, spec={})
        result = combine(internal_where, compiled)
        assert result == "(internal WHERE) AND (user WHERE)"

    def test_combine_empty_parts_returns_none(self):
        where = None
        compiled = None
        result = combine(where, compiled)
        assert result is None


class TestBoundaryConditions:
    def test_max_int32_value(self):
        result = _check_int("field", "eq", 2**31 - 1)
        assert result == 2**31 - 1

    def test_min_int32_value(self):
        result = _check_int("field", "eq", -(2**31))
        assert result == -(2**31)

    def test_max_string_length_boundary(self):
        max_len = _MAX_STRING_LENGTH
        valid_str = "a" * max_len
        result = _check_string("field", "eq", valid_str)
        assert result == valid_str

    def test_max_in_items_boundary(self):
        max_items = _MAX_IN_ITEMS
        items = [f"item{i}" for i in range(max_items)]
        result = _compile_field(
            "document_id", "document_id", "string", ("in",), items
        )
        assert len(result) == 1

    def test_max_in_items_plus_one_raises_error(self):
        max_items = _MAX_IN_ITEMS + 1
        items = [f"item{i}" for i in range(max_items)]
        with pytest.raises(FilterError, match="_MAX_IN_ITEMS"):
            _compile_field(
                "document_id", "document_id", "string", ("in",), items
            )

    def test_empty_string_in_list_raises_error(self):
        with pytest.raises(FilterError, match="is an empty list"):
            _compile_field(
                "document_id", "document_id", "string", ("in",), [""]
            )

    def test_single_char_value_in_list(self):
        result = _compile_field(
            "document_id", "document_id", "string", ("in",), ["a"]
        )
        assert result == ["document_id IN ('a')"]


class TestFieldMapping:
    def test_document_id_allowed_ops(self):
        field_info = _FIELD_BY_NAME["document_id"]
        assert field_info[2] == "string"
        assert set(field_info[3]) == {"eq", "in", "contains"}

    def test_chunk_index_allowed_ops(self):
        field_info = _FIELD_BY_NAME["chunk_index"]
        assert field_info[2] == "int"
        assert set(field_info[3]) == {"eq", "in", "gt", "gte", "lt", "lte"}

    def test_document_name_only_contains_op(self):
        field_info = _FIELD_BY_NAME["document_name"]
        assert field_info[2] == "string"
        assert set(field_info[3]) == {"contains"}


class TestCompileFiltersEdgeCases:
    def test_multiple_fields_anded(self):
        filters = {
            "document_id": {"eq": "test.pdf"},
            "chunk_index": {"gte": 0},
        }
        result = compile_filters(filters)
        assert "document_id" in result.where
        assert "chunk_index" in result.where

    def test_field_order_preserved(self):
        filters = {
            "chunk_index": {"gte": 0},
            "document_id": {"eq": "test.pdf"},
        }
        result = compile_filters(filters)
        # Fields are emitted in canonical order, not dict order
        assert result.where.startswith("document_id")

    def test_complex_filter_with_wildcards(self):
        filters = {
            "document_name": {"contains": "nda"},
        }
        result = compile_filters(filters)
        assert "LIKE" in result.where
        assert "ESCAPE" in result.where
