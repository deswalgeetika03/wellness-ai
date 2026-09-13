import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

TOP_K = 3

TEST_CASES = [
    {
        "topic": "Stress",
        "previous_user": "How can I manage daily stress?",
        "previous_assistant": "You can try relaxation techniques, make time for enjoyable activities, and use healthy coping strategies.",
        "current": "What should I try first?",
        "expected": "01",
    },
    {
        "topic": "Stress coping",
        "previous_user": "What are healthy ways to cope with stress?",
        "previous_assistant": "Healthy coping can include relaxation, physical activity, social support, and making time for enjoyable activities.",
        "current": "What can I do about it?",
        "expected": "02",
    },
    {
        "topic": "Anxiety",
        "previous_user": "What are symptoms of anxiety?",
        "previous_assistant": "Anxiety can involve excessive worry and may include physical or emotional symptoms.",
        "current": "Which ones should I look out for?",
        "expected": "04",
    },
    {
        "topic": "Panic",
        "previous_user": "What is a panic attack?",
        "previous_assistant": "A panic attack can involve sudden intense fear and physical symptoms such as a racing heart or difficulty breathing.",
        "current": "What happens during one?",
        "expected": "08",
    },
    {
        "topic": "Sleep",
        "previous_user": "How can I sleep better?",
        "previous_assistant": "Healthy sleep habits can include keeping a regular schedule and creating a comfortable sleep environment.",
        "current": "What should I change first?",
        "expected": "05",
    },
    {
        "topic": "Eating disorders",
        "previous_user": "What are eating disorders?",
        "previous_assistant": "Eating disorders are mental health conditions involving disturbances in eating behavior and related thoughts or emotions.",
        "current": "Where can I get help?",
        "expected": "09",
    },
    {
        "topic": "Depression",
        "previous_user": "What is depression?",
        "previous_assistant": "Depression can involve persistent low mood and loss of interest or pleasure.",
        "current": "What are the main signs?",
        "expected": "12",
    },
    {
        "topic": "Mental health",
        "previous_user": "What does it mean to have good mental health?",
        "previous_assistant": "Mental health includes emotional, psychological, and social well-being.",
        "current": "How can I improve it?",
        "expected": "03",
    },
]


def retrieve(vector_db, query):
    return vector_db.similarity_search(query, k=TOP_K)


def evaluate(vector_db, strategy):
    top1 = 0
    top3 = 0

    print()
    print("=" * 90)
    print(strategy)
    print("=" * 90)

    for case in TEST_CASES:
        previous_user = case["previous_user"]
        previous_assistant = case["previous_assistant"]
        current = case["current"]
        expected = case["expected"]

        if strategy == "CURRENT QUESTION ONLY":
            query = current

        elif strategy == "PREVIOUS USER + CURRENT QUESTION":
            query = f"{previous_user} {current}"

        elif strategy == "PREVIOUS USER + PREVIOUS ASSISTANT + CURRENT QUESTION":
            query = f"{previous_user} {previous_assistant} {current}"

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
        print(f"[{status}] {case['topic']}")
        print(f"Previous user:      {previous_user}")
        print(f"Previous assistant: {previous_assistant}")
        print(f"Current:            {current}")
        print(f"Query:              {query}")
        print(f"Expected:           {expected}")
        print(f"Got:                {list(zip(ids, titles))}")

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

    results = {}

    strategies = [
        "CURRENT QUESTION ONLY",
        "PREVIOUS USER + CURRENT QUESTION",
        "PREVIOUS USER + PREVIOUS ASSISTANT + CURRENT QUESTION",
    ]

    for strategy in strategies:
        results[strategy] = evaluate(vector_db, strategy)

    print()
    print("=" * 90)
    print("FINAL COMPARISON")
    print("=" * 90)

    for strategy, (top1, top3, total) in results.items():
        print(
            f"{strategy}: "
            f"Top-1 {top1}/{total} ({top1 / total * 100:.1f}%) | "
            f"Top-3 {top3}/{total} ({top3 / total * 100:.1f}%)"
        )

    baseline_top1, baseline_top3, total = results["CURRENT QUESTION ONLY"]

    print()
    print("CHANGE VS CURRENT-QUESTION BASELINE")

    for strategy in strategies[1:]:
        top1, top3, _ = results[strategy]

        print(
            f"{strategy}: "
            f"Top-1 {(top1 - baseline_top1) / total * 100:+.1f} pp | "
            f"Top-3 {(top3 - baseline_top3) / total * 100:+.1f} pp"
        )


if __name__ == "__main__":
    main()
