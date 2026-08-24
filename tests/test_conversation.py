from app.conversation import ConversationManager


def test_session_is_created():
    manager = ConversationManager()

    session = manager.get_session("session-1")

    assert session is not None
    assert session.last_order_id is None
    assert session.last_topic is None


def test_messages_are_preserved():
    manager = ConversationManager()

    manager.add_user_message(
        "session-1",
        "Where is ORD-1007?",
    )

    manager.add_assistant_message(
        "session-1",
        "Your order is shipped.",
    )

    session = manager.get_context("session-1")

    assert len(session.messages) == 2
    assert session.messages[0]["role"] == "user"
    assert session.messages[1]["role"] == "assistant"


def test_order_context_is_preserved():
    manager = ConversationManager()

    manager.update_order_id(
        "session-1",
        "ORD-1007",
    )

    session = manager.get_context("session-1")

    assert session.last_order_id == "ORD-1007"


def test_sessions_are_isolated():
    manager = ConversationManager()

    manager.update_order_id(
        "session-1",
        "ORD-1007",
    )

    manager.update_order_id(
        "session-2",
        "ORD-1011",
    )

    session_one = manager.get_context("session-1")
    session_two = manager.get_context("session-2")

    assert session_one.last_order_id == "ORD-1007"
    assert session_two.last_order_id == "ORD-1011"


def test_recent_messages_returns_latest_messages():
    manager = ConversationManager()

    for index in range(10):
        manager.add_user_message(
            "session-1",
            f"message-{index}",
        )

    session = manager.get_context("session-1")

    recent = session.recent_messages(limit=3)

    assert len(recent) == 3
    assert recent[0]["content"] == "message-7"
    assert recent[1]["content"] == "message-8"
    assert recent[2]["content"] == "message-9"


def test_sources_are_preserved():
    manager = ConversationManager()

    sources = [
        "01-returns-policy-current.md — Standard return window",
        "09-trailplus-membership.md — Return window",
    ]

    manager.update_sources(
        "session-1",
        sources,
    )

    session = manager.get_context("session-1")

    assert session.last_sources == sources


def test_clear_session_removes_context():
    manager = ConversationManager()

    manager.add_user_message(
        "session-1",
        "Where is ORD-1007?",
    )

    manager.update_order_id(
        "session-1",
        "ORD-1007",
    )

    manager.clear_session("session-1")

    session = manager.get_context("session-1")

    assert session.messages == []
    assert session.last_order_id is None
    assert session.last_topic is None