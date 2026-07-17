from job_market_ai_agent.analysis.openai_client import _build_request_payload, _extract_output_text


def test_build_request_payload_uses_json_schema_format() -> None:
    payload = _build_request_payload({"title": "AI Engineer"}, model="test-model")

    assert payload["model"] == "test-model"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["name"] == "job_analysis"


def test_extract_output_text_from_responses_payload() -> None:
    payload = {
        "output": [
            {
                "content": [
                    {"type": "output_text", "text": "{\"role_category\":\"AI Engineer\"}"}
                ]
            }
        ]
    }

    assert _extract_output_text(payload) == "{\"role_category\":\"AI Engineer\"}"

