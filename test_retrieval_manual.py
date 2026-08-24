from app.retrieval import KnowledgeBase


kb = KnowledgeBase()

documents = kb.load_documents()

print(f"Loaded chunks: {len(documents)}")

for document in documents[:5]:
    print()
    print("FILE:", document.filename)
    print("HEADING:", document.heading)
    print("METADATA:", document.metadata)
    print("TEXT:", document.text[:200])

print("\nTesting search...\n")

results = kb.search(
    "What is the return window?",
    top_k=5,
)

for result in results:
    print(
        f"{result.score:.3f} | "
        f"{result.chunk.filename} | "
        f"{result.chunk.heading}"
    )