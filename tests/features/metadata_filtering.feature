Feature: Metadata filtering
  Users can restrict document searches using supported metadata filters.
  These scenarios verify the public filter compiler, not the full retrieval application.

  Scenario: Apply a valid metadata filter
    Given a document identifier filter for "report.pdf"
    When the metadata filter is compiled
    Then the exact document equality condition is returned

  Scenario: Reject an invalid metadata filter
    Given a metadata filter with an unsupported field
    When the metadata filter is compiled
    Then a filter validation error identifies the unsupported field

  Scenario: Continue without filtering when no filter is supplied
    Given no metadata filter is supplied
    When the metadata filter is compiled
    Then no compiled filter is returned
