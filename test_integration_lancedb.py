"""Integration tests: filters.py  +  a REAL LanceDB table.

Each test compiles a filter with the production code and executes the resulting
where-clause in LanceDB, so we verify that what the module *emits* is what the
database *does* -- something unit tests on the SQL string cannot show.

Test level: integration (two real components: filter compiler + LanceDB engine).
"""
import pytest

lancedb = pytest.importorskip("lancedb")

from rag_system.retrieval.filters import FilterError, combine, compile_filters

ROWS = [  # (document_id, chunk_index)
    ("01_acquisition_agreement.pdf", 0), ("01_acquisition_agreement.pdf", 1),
    ("01_acquisition_agreement.pdf", 2), ("01_acquisitionXagreement.pdf", 0),
    ("07_nda.pdf", 0), ("07_nda.pdf", 1),
    ("03_ip_certification.pdf", 0), ("100%_complete.pdf", 0),
]


@pytest.fixture()
def table(tmp_path):
    db = lancedb.connect(str(tmp_path))
    data = [{"vector": [float(i), 0.0, 0.0, 1.0], "text": f"chunk {d}#{i}",
             "chunk_id": f"{d}#{i}", "document_id": d, "chunk_index": i, "metadata": "{}"}
            for d, i in ROWS]
    return db.create_table("text_pages", data=data)


def run(table, where):
    q = table.search([0.0, 0.0, 0.0, 1.0]).limit(100)
    if where:
        q = q.where(where)
    return {r["chunk_id"] for r in q.to_list()}


def all_ids():
    return {f"{d}#{i}" for d, i in ROWS}


def test_eq_filter_returns_only_that_document(table):
    got = run(table, compile_filters({"document_id": "07_nda.pdf"}).where)
    assert got == {"07_nda.pdf#0", "07_nda.pdf#1"}


def test_in_filter_returns_union_of_documents(table):
    where = compile_filters({"document_id": {"in": ["07_nda.pdf", "03_ip_certification.pdf"]}}).where
    assert run(table, where) == {"07_nda.pdf#0", "07_nda.pdf#1", "03_ip_certification.pdf#0"}


def test_chunk_index_range_is_inclusive_at_both_ends(table):
    where = compile_filters({"document_id": "01_acquisition_agreement.pdf",
                             "chunk_index": {"gte": 1, "lte": 2}}).where
    assert run(table, where) == {"01_acquisition_agreement.pdf#1", "01_acquisition_agreement.pdf#2"}


def test_contains_treats_underscore_literally_not_as_wildcard(table):
    # '_' is a LIKE wildcard; without correct escaping this would also match '...acquisitionXagreement.pdf'
    where = compile_filters({"document_name": {"contains": "acquisition_agreement"}}).where
    got = run(table, where)
    assert got == {"01_acquisition_agreement.pdf#0", "01_acquisition_agreement.pdf#1", "01_acquisition_agreement.pdf#2"}
    assert "01_acquisitionXagreement.pdf#0" not in got


def test_contains_treats_percent_literally(table):
    where = compile_filters({"document_name": {"contains": "100%"}}).where
    assert run(table, where) == {"100%_complete.pdf#0"}


def test_combine_narrows_internal_restriction_never_widens(table):
    internal = "document_id = '01_acquisition_agreement.pdf'"
    user = compile_filters({"chunk_index": {"lte": 1}})
    got = run(table, combine(internal, user))
    assert got == {"01_acquisition_agreement.pdf#0", "01_acquisition_agreement.pdf#1"}


def test_field_order_in_request_does_not_change_database_result(table):
    a = compile_filters({"document_id": "07_nda.pdf", "chunk_index": {"gte": 1}})
    b = compile_filters({"chunk_index": {"gte": 1}, "document_id": "07_nda.pdf"})
    assert a.where == b.where
    assert run(table, a.where) == run(table, b.where) == {"07_nda.pdf#1"}


def test_filter_matching_nothing_returns_empty_not_everything(table):
    assert run(table, compile_filters({"document_id": "does_not_exist.pdf"}).where) == set()


@pytest.mark.parametrize("bad", [
    {"document_id": "x' OR '1'='1"},
    {"document_id": "x'; DROP TABLE text_pages; --"},
    {"document_name": {"contains": 'a"b'}},
])
def test_injection_attempts_are_rejected_before_reaching_database(table, bad):
    with pytest.raises(FilterError):
        compile_filters(bad)
    assert run(table, None) == all_ids()          # table untouched, still fully queryable
