from app.retrieval import KnowledgeBase


def main():
    kb = KnowledgeBase()

    count = kb.build_index()

    print(f"Indexed {count} document chunks.")


if __name__ == "__main__":
    main()