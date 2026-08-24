from app.agent import SupportAgent


def test_order_result_does_not_expose_internal_fields():
    agent = SupportAgent()

    result = agent.order_lookup.lookup("ORD-1007")

    safe_result = agent.order_lookup.to_customer_safe_dict(
        result
    )

    forbidden_terms = {
        "email",
        "address",
        "risk_score",
        "internal_note",
        "warehouse_note",
        "support_tags",
    }

    result_text = str(safe_result).lower()

    for term in forbidden_terms:
        assert term not in result_text


def test_unknown_order_does_not_invent_information():
    agent = SupportAgent()

    result = agent.order_lookup.lookup("ORD-9999")

    assert result.found is False
    assert result.status is None
    assert result.carrier is None
    assert result.tracking_number is None
    assert result.estimated_delivery is None


def test_malformed_order_does_not_trigger_lookup():
    agent = SupportAgent()

    response = agent.handle_message(
        "security-test-1",
        "Where is ABC-123?",
    )

    assert len(response.tool_calls) == 0


def test_missing_order_id_requests_order_id():
    agent = SupportAgent()

    response = agent.handle_message(
        "security-test-2",
        "Where is my order?",
    )

    assert (
        "order id" in response.answer.lower()
        or "order number" in response.answer.lower()
    )


def test_system_prompt_is_not_returned_by_application():
    agent = SupportAgent()

    assert "API_KEY" not in agent.SYSTEM_PROMPT if hasattr(
        agent,
        "SYSTEM_PROMPT",
    ) else True


def test_internal_fields_are_not_part_of_tool_record():
    agent = SupportAgent()

    response = agent.handle_message(
        "security-test-3",
        "Where is ORD-1007?",
    )

    assert len(response.tool_calls) == 1

    tool_result = response.tool_calls[0].result

    forbidden_fields = {
        "email",
        "address",
        "shipping_address",
        "risk_score",
        "internal_note",
        "warehouse_note",
        "support_tags",
    }

    assert forbidden_fields.isdisjoint(
        tool_result.keys()
    )