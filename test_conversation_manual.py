from app.conversation import ConversationManager


manager = ConversationManager()

manager.add_user_message(
    "session-1",
    "Where is ORD-1007?",
)

manager.update_order_id(
    "session-1",
    "ORD-1007",
)

manager.add_assistant_message(
    "session-1",
    "Your order is shipped.",
)

manager.add_user_message(
    "session-1",
    "When will it arrive?",
)

context = manager.get_context("session-1")

print("Order:", context.last_order_id)
print("Topic:", context.last_topic)
print("Messages:", context.recent_messages())

other_context = manager.get_context("session-2")

print("Other session order:", other_context.last_order_id)