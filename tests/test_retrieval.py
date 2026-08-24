from app.retrieval import KnowledgeBase


def test_documents_are_loaded():
    kb = KnowledgeBase()

    documents = kb.load_documents()

    assert len(documents) > 0


def test_front_matter_is_preserved():
    kb = KnowledgeBase()

    documents = kb.load_documents()

    current_policy = next(
        document
        for document in documents
        if document.filename
        == "01-returns-policy-current.md"
    )

    assert current_policy.metadata["status"] == "active"
    assert current_policy.metadata["audience"] == "customer"
    assert (
        current_policy.metadata["policy_authority"]
        == "official"
    )


def test_headings_are_preserved():
    kb = KnowledgeBase()

    documents = kb.load_documents()

    headings = {
        document.heading
        for document in documents
        if document.filename
        == "01-returns-policy-current.md"
    }

    assert "Standard return window" in headings


def test_current_returns_policy_ranks_above_legacy():
    kb = KnowledgeBase()

    results = kb.search(
        "What is the return window?",
        top_k=8,
    )

    assert len(results) > 0

    top_result = results[0]

    assert (
        top_result.chunk.filename
        == "01-returns-policy-current.md"
    )


def test_search_returns_relevant_heading():
    kb = KnowledgeBase()

    results = kb.search(
        "What is the return window?",
        top_k=8,
    )

    matching_results = [
        result
        for result in results
        if (
            result.chunk.filename
            == "01-returns-policy-current.md"
            and result.chunk.heading
            == "Standard return window"
        )
    ]

    assert len(matching_results) > 0


def test_superseded_policy_is_penalized():
    kb = KnowledgeBase()

    results = kb.search(
        "What is the return window?",
        top_k=8,
    )

    current_results = [
        result
        for result in results
        if (
            result.chunk.filename
            == "01-returns-policy-current.md"
        )
    ]

    legacy_results = [
        result
        for result in results
        if (
            result.chunk.filename
            == "02-returns-policy-legacy.md"
        )
    ]

    assert current_results

    if legacy_results:
        assert (
            max(
                result.score
                for result in current_results
            )
            > max(
                result.score
                for result in legacy_results
            )
        )


def test_sources_contain_filename_and_heading():
    kb = KnowledgeBase()

    results = kb.search(
        "What is the return window?",
        top_k=5,
    )

    sources = kb.format_sources(results)

    assert len(sources) > 0

    for source in sources:
        assert ".md" in source
        assert " — " in source