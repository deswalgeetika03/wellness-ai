import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

TOP_K = 3

TEST_CASES = [
    ("How can I manage daily stress?", "What should I try first?", "01"),
    ("What are healthy ways to cope with stress?", "What can I do about it?", "02"),
    ("What are symptoms of anxiety?", "Which ones should I look out for?", "04"),
    ("What is a panic attack?", "What happens during one?", "08"),
    ("How can I sleep better?", "What should I change first?", "05"),
    ("What are eating disorders?", "Where can I get help?", "09"),
    ("What is depression?", "What are the main signs?", "12"),
    ("What does it mean to have good mental health?", "How can I improve it?", "03"),
]


def retrieve(vector_db, query):
    return vector_db.similarity_search(query, k=TOP_K)


def evaluate(vector_db, history_aware=False):
    top1 = 0
    top3 = 0

    print()
    print("=" * 80)
    print(
        "HISTORY-AWARE RETRIEVAL"
        if history_aware
        else "CURRENT-QUESTION-ONLY RETRIEVAL"
    )
    print("=" * 80)

    for previous, current, expected in TEST_CASES:
        query = (
            f"{previous} {current}"
            if history_aware
            else current
        )

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
        print(f"[{status}]")
        print(f"Previous: {previous}")
        print(f"Current:  {current}")
        print(f"Query:    {query}")
        print(f"Expected: {expected}")
        print(f"Got:      {list(zip(ids, titles))}")

    return top1, top3


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

    baseline_top1, baseline_top3 = evaluate(
        vector_db,
        history_aware=False,
    )

    history_top1, history_top3 = evaluate(
        vector_db,
        history_aware=True,
    )

    total = len(TEST_CASES)

    print()
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)

    print(
        f"Current-question only: "
        f"Top-1 {baseline_top1}/{total} "
        f"({baseline_top1 / total * 100:.1f}%) | "
        f"Top-3 {baseline_top3}/{total} "
        f"({baseline_top3 / total * 100:.1f}%)"
    )

    print(
        f"History-aware:         "
        f"Top-1 {history_top1}/{total} "
        f"({history_top1 / total * 100:.1f}%) | "
        f"Top-3 {history_top3}/{total} "
        f"({history_top3 / total * 100:.1f}%)"
    )

    print(
        f"Top-1 change: "
        f"{(history_top1 - baseline_top1) / total * 100:+.1f} pp"
    )

    print(
        f"Top-3 change: "
        f"{(history_top3 - baseline_top3) / total * 100:+.1f} pp"
    )


if __name__ == "__main__":
    main()
