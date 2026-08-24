from dataclasses import dataclass, field


@dataclass
class ConversationState:
    messages: list[dict[str, str]] = field(default_factory=list)
    last_order_id: str | None = None
    last_topic: str | None = None
    last_sources: list[str] = field(default_factory=list)

    def add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    def set_order_id(
        self,
        order_id: str | None,
    ) -> None:
        self.last_order_id = order_id

    def set_topic(
        self,
        topic: str | None,
    ) -> None:
        self.last_topic = topic

    def set_sources(
        self,
        sources: list[str],
    ) -> None:
        self.last_sources = sources

    def recent_messages(
        self,
        limit: int = 6,
    ) -> list[dict[str, str]]:
        return self.messages[-limit:]

    def clear(self) -> None:
        self.messages.clear()
        self.last_order_id = None
        self.last_topic = None
        self.last_sources.clear()


class ConversationManager:
    def __init__(self):
        self.sessions: dict[str, ConversationState] = {}

    def get_session(
        self,
        session_id: str,
    ) -> ConversationState:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState()

        return self.sessions[session_id]

    def add_user_message(
        self,
        session_id: str,
        message: str,
    ) -> ConversationState:
        session = self.get_session(session_id)
        session.add_message("user", message)
        return session

    def add_assistant_message(
        self,
        session_id: str,
        message: str,
    ) -> ConversationState:
        session = self.get_session(session_id)
        session.add_message("assistant", message)
        return session

    def update_order_id(
        self,
        session_id: str,
        order_id: str | None,
    ) -> None:
        session = self.get_session(session_id)
        session.set_order_id(order_id)

    def update_topic(
        self,
        session_id: str,
        topic: str | None,
    ) -> None:
        session = self.get_session(session_id)
        session.set_topic(topic)

    def update_sources(
        self,
        session_id: str,
        sources: list[str],
    ) -> None:
        session = self.get_session(session_id)
        session.set_sources(sources)

    def get_context(
        self,
        session_id: str,
    ) -> ConversationState:
        return self.get_session(session_id)

    def clear_session(
        self,
        session_id: str,
    ) -> None:
        if session_id in self.sessions:
            self.sessions[session_id].clear()