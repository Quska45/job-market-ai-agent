from job_market_ai_agent.core.hashing import build_content_hash


def test_build_content_hash_is_stable_for_same_payload() -> None:
    payload = {
        "source": "saramin",
        "title": "AI Engineer",
        "company": "Example",
        "description": "Build RAG systems",
    }

    assert build_content_hash(payload) == build_content_hash(payload)


def test_build_content_hash_is_independent_of_key_order() -> None:
    left = {"title": "AI Engineer", "company": "Example"}
    right = {"company": "Example", "title": "AI Engineer"}

    assert build_content_hash(left) == build_content_hash(right)

