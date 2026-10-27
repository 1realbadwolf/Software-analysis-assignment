"""New BDD verification of the public filter compiler; component level."""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from rag_system.retrieval.filters import CompiledFilter, FilterError, compile_filters

scenarios("features/metadata_filtering.feature")

@given(parsers.parse('a document identifier filter for "{document_id}"'), target_fixture="filter_input")
def valid_filter(document_id):
    return {"document_id": {"eq": document_id}}

@given("a metadata filter with an unsupported field", target_fixture="filter_input")
def unsupported_filter():
    return {"unknown_field": {"eq": "value"}}

@given("no metadata filter is supplied", target_fixture="filter_input")
def no_filter():
    return None

@when("the metadata filter is compiled", target_fixture="outcome")
def compile_input(filter_input):
    try:
        return {"result": compile_filters(filter_input), "error": None}
    except FilterError as error:
        return {"result": None, "error": error}

@then("the exact document equality condition is returned")
def exact_condition(outcome):
    assert outcome["error"] is None
    compiled = outcome["result"]
    assert isinstance(compiled, CompiledFilter)
    assert compiled.where == "document_id = 'report.pdf'"
    assert compiled.spec == {"document_id": {"eq": "report.pdf"}}

@then("a filter validation error identifies the unsupported field")
def invalid_condition(outcome):
    assert isinstance(outcome["error"], FilterError)
    assert "Unsupported filter field" in str(outcome["error"])
    assert "unknown_field" in str(outcome["error"])
    assert outcome["result"] is None

@then("no compiled filter is returned")
def no_condition(outcome):
    assert outcome["error"] is None
    assert outcome["result"] is None
