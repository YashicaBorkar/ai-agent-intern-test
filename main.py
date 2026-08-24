from app.agent import SupportAgent


def main():
    agent = SupportAgent()
    session_id = "cli-session"

    print("Aster & Row Support Agent")
    print("Type 'exit' to quit.")
    print()

    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if user_message.lower() == "exit":
            print("Goodbye.")
            break

        if not user_message:
            continue

        response = agent.handle_message(
            session_id,
            user_message,
        )

        print()
        print("Agent:", response.answer)

        if response.sources:
            print()
            print("Sources:")

            for source in response.sources:
                print(f"- {source}")

        print(
            f"Human handoff: "
            f"{'Yes' if response.human_handoff else 'No'}"
        )

        print()


if __name__ == "__main__":
    main()