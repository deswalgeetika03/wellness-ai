import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

TOP_K = 3

# Each case contains an older unrelated topic followed by the
# immediately previous topic that the current follow-up refers to.
TEST_CASES = [
    {
        "name": "Sleep -> Stress -> Stress follow-up",
        "older_user": "How can I improve my sleep?",
        "previous_user": "What are healthy ways to manage stress?",
        "current": "What should I try first?",
        "expected": "02",
    },
    {
        "name": "Stress -> Anxiety -> Anxiety follow-up",
        "older_user": "What are some ways to manage stress?",
        "previous_user": "What are symptoms of anxiety?",
        "current": "Which ones should I look out for?",
        "expected": "04",
    },
    {
        "name": "Depression -> Panic -> Panic follow-up",
        "older_user": "What is depression?",
        "previous_user": "What is a panic attack?",
        "current": "What happens during one?",
        "expected": "08",
    },
    {
        "name": "Anxiety -> Sleep -> Sleep follow-up",
        "older_user": "What are symptoms of anxiety?",
        "previous_user": "How can I sleep better?",
        "current": "What should I change first?",
        "expected": "05",
    },
    {
        "name": "Mental health -> Eating disorders -> Eating-disorder follow-up",
        "older_user": "What does good mental health mean?",
        "previous_user": "What are eating disorders?",
        "current": "Where can I get help?",
        "expected": "09",
    },
    {
        "name": "Sleep -> Depression -> Depression follow-up",
        "older_user": "What are healthy sleep habits?",
        "previous_user": "What is depression?",
        "current": "What are the main signs?",
        "expected": "12",
    },
    {
        "name": "Eating disorders -> Mental health -> Mental-health follow-up",
        "older_user": "What are eating disorders?",
        "previous_user": "What does it mean to have good mental health?",
        "current": "How can I improve it?",
        "expected": "03",
    },
    {
        "name": "Panic -> Stress -> Stress follow-up",
        "older_user": "What is a panic attack?",
        "previous_user": "How can I manage daily stress?",
        "current": "What should I try first?",
        "expected": "01",
    },
]


def retrieve(vector_db, query):
    return vector_db.similarity_search(query, k=TOP_K)


def evaluate(vector_db, strategy):
    top1 = 0
    top3 = 0

    print()
    print("=" * 95)
    print(strategy)
    print("=" * 95)

    for case in TEST_CASES:
        older = case["older_user"]
        previous = case["previous_user"]
        current = case["current"]
        expected = case["expected"]

        if strategy == "CURRENT ONLY":
            query = current

        elif strategy == "PREVIOUS USER + CURRENT":
            query = f"{previous} {current}"

        elif strategy == "OLDER + PREVIOUS + CURRENT":
            query = f"{older} {previous} {current}"

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        results = retrieve(vector_db, query)

        ids = [
            str(doc.metadata.get("source_id", "?"))
            for doc in results
        ]

        titles = [
            doc.metadata.get("title", "Unknown")
            for doc in results
        ]

        hit1 = bool(ids) and ids[0] == expected
        hit3 = expected in ids

        top1 += int(hit1)
        top3 += int(hit3)

        status = (
            "PASS (top-1)"
            if hit1
            else "PASS (top-3 only)"
            if hit3
            else "FAIL"
        )

        print()
        print(f"[{status}] {case['name']}")
        print(f"Older user:   {older}")
        print(f"Previous:     {previous}")
        print(f"Current:      {current}")
        print(f"Query:        {query}")
        print(f"Expected:     {expected}")
        print(f"Retrieved:    {list(zip(ids, titles))}")

    total = len(TEST_CASES)

    return top1, top3, total


def main():
    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print("Connecting to ChromaDB...")

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    strategies = [
        "CURRENT ONLY",
        "PREVIOUS USER + CURRENT",
        "OLDER + PREVIOUS + CURRENT",
    ]

    results = {}

    for strategy in strategies:
        results[strategy] = evaluate(vector_db, strategy)

    print()
    print("=" * 95)
    print("FINAL COMPARISON")
    print("=" * 95)

    for strategy, (top1, top3, total) in results.items():
        print(
            f"{strategy}: "
            f"Top-1 {top1}/{total} ({top1 / total * 100:.1f}%) | "
            f"Top-3 {top3}/{total} ({top3 / total * 100:.1f}%)"
        )

    baseline_top1, baseline_top3, total = results["CURRENT ONLY"]

    print()
    print("CHANGE VS CURRENT-QUESTION BASELINE")

    for strategy in strategies[1:]:
        top1, top3, _ = results[strategy]

        print(
            f"{strategy}: "
            f"Top-1 {(top1 - baseline_top1) / total * 100:+.1f} pp | "
            f"Top-3 {(top3 - baseline_top3) / total * 100:+.1f} pp"
        )

    previous_top1, previous_top3, _ = results[
        "PREVIOUS USER + CURRENT"
    ]

    older_top1, older_top3, _ = results[
        "OLDER + PREVIOUS + CURRENT"
    ]

    print()
    print("OLDER HISTORY EFFECT")

    print(
        f"Adding older user message: "
        f"Top-1 {(older_top1 - previous_top1) / total * 100:+.1f} pp | "
        f"Top-3 {(older_top3 - previous_top3) / total * 100:+.1f} pp"
    )


if __name__ == "__main__":
    main()
