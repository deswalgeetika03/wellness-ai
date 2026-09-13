import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

TOP_K = 3

# "follow_up" cases should benefit from previous-user context.
# "standalone" cases should NOT need previous context.
TEST_CASES = [
    {
        "name": "Stress follow-up",
        "previous_user": "How can I manage daily stress?",
        "current": "What should I try first?",
        "expected": "01",
        "type": "follow_up",
    },
    {
        "name": "Stress coping follow-up",
        "previous_user": "What are healthy ways to cope with stress?",
        "current": "What can I do about it?",
        "expected": "02",
        "type": "follow_up",
    },
    {
        "name": "Anxiety follow-up",
        "previous_user": "What are symptoms of anxiety?",
        "current": "Which ones should I look out for?",
        "expected": "04",
        "type": "follow_up",
    },
    {
        "name": "Panic follow-up",
        "previous_user": "What is a panic attack?",
        "current": "What happens during one?",
        "expected": "08",
        "type": "follow_up",
    },
    {
        "name": "Sleep follow-up",
        "previous_user": "How can I sleep better?",
        "current": "What should I change first?",
        "expected": "05",
        "type": "follow_up",
    },
    {
        "name": "Eating-disorder follow-up",
        "previous_user": "What are eating disorders?",
        "current": "Where can I get help?",
        "expected": "09",
        "type": "follow_up",
    },
    {
        "name": "Depression follow-up",
        "previous_user": "What is depression?",
        "current": "What are the main signs?",
        "expected": "12",
        "type": "follow_up",
    },
    {
        "name": "Mental-health follow-up",
        "previous_user": "What does it mean to have good mental health?",
        "current": "How can I improve it?",
        "expected": "03",
        "type": "follow_up",
    },

    # Standalone questions with unrelated previous topics.
    {
        "name": "Standalone depression",
        "previous_user": "How can I improve my sleep?",
        "current": "What is depression?",
        "expected": "12",
        "type": "standalone",
    },
    {
        "name": "Standalone panic",
        "previous_user": "How can I manage stress?",
        "current": "What is a panic attack?",
        "expected": "08",
        "type": "standalone",
    },
    {
        "name": "Standalone sleep",
        "previous_user": "What are symptoms of anxiety?",
        "current": "How can I sleep better?",
        "expected": "05",
        "type": "standalone",
    },
    {
        "name": "Standalone anxiety",
        "previous_user": "What is depression?",
        "current": "What are symptoms of anxiety?",
        "expected": "04",
        "type": "standalone",
    },
    {
        "name": "Standalone eating disorders",
        "previous_user": "What are healthy sleep habits?",
        "current": "What are eating disorders?",
        "expected": "09",
        "type": "standalone",
    },
    {
        "name": "Standalone mental health",
        "previous_user": "What is a panic attack?",
        "current": "What does good mental health mean?",
        "expected": "03",
        "type": "standalone",
    },
    {
        "name": "Standalone stress",
        "previous_user": "What is depression?",
        "current": "What are some ways to manage stress?",
        "expected": "02",
        "type": "standalone",
    },
    {
        "name": "Standalone depression treatment",
        "previous_user": "How can I sleep better?",
        "current": "How is depression treated?",
        "expected": "12",
        "type": "standalone",
    },
]


def retrieve(vector_db, query):
    return vector_db.similarity_search(query, k=TOP_K)


def looks_like_follow_up(question):
    """
    Small deterministic heuristic for evaluation only.

    The question is treated as context-dependent when it contains
    pronouns/references or generic follow-up phrasing that is difficult
    to interpret without the previous user message.
    """
    q = question.lower().strip()

    patterns = [
        "what should i try first",
        "what should i change first",
        "what can i do about it",
        "which ones should i look out for",
        "what happens during one",
        "where can i get help",
        "what are the main signs",
        "how can i improve it",
        "what about it",
        "what about that",
        "how can i manage it",
        "how do i manage it",
        "what should i do next",
        "what should i try",
        "how can i improve that",
    ]

    return any(pattern in q for pattern in patterns)


def evaluate(vector_db, strategy):
    total_top1 = 0
    total_top3 = 0

    follow_top1 = 0
    follow_top3 = 0
    follow_total = 0

    standalone_top1 = 0
    standalone_top3 = 0
    standalone_total = 0

    print()
    print("=" * 95)
    print(strategy)
    print("=" * 95)

    for case in TEST_CASES:
        previous = case["previous_user"]
        current = case["current"]
        expected = case["expected"]
        case_type = case["type"]

        if strategy == "CURRENT ONLY":
            query = current
            used_history = False

        elif strategy == "ALWAYS PREVIOUS USER + CURRENT":
            query = f"{previous} {current}"
            used_history = True

        elif strategy == "SELECTIVE HISTORY":
            used_history = looks_like_follow_up(current)

            if used_history:
                query = f"{previous} {current}"
            else:
                query = current

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

        total_top1 += int(hit1)
        total_top3 += int(hit3)

        if case_type == "follow_up":
            follow_total += 1
            follow_top1 += int(hit1)
            follow_top3 += int(hit3)
        else:
            standalone_total += 1
            standalone_top1 += int(hit1)
            standalone_top3 += int(hit3)

        status = (
            "PASS (top-1)"
            if hit1
            else "PASS (top-3 only)"
            if hit3
            else "FAIL"
        )

        print()
        print(f"[{status}] {case['name']} [{case_type}]")
        print(f"Previous:     {previous}")
        print(f"Current:      {current}")
        print(f"Used history: {used_history}")
        print(f"Query:        {query}")
        print(f"Expected:     {expected}")
        print(f"Retrieved:    {list(zip(ids, titles))}")

    total = len(TEST_CASES)

    return {
        "top1": total_top1,
        "top3": total_top3,
        "total": total,
        "follow_top1": follow_top1,
        "follow_top3": follow_top3,
        "follow_total": follow_total,
        "standalone_top1": standalone_top1,
        "standalone_top3": standalone_top3,
        "standalone_total": standalone_total,
    }


def pct(value, total):
    return value / total * 100 if total else 0.0


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
        "ALWAYS PREVIOUS USER + CURRENT",
        "SELECTIVE HISTORY",
    ]

    results = {}

    for strategy in strategies:
        results[strategy] = evaluate(vector_db, strategy)

    print()
    print("=" * 95)
    print("FINAL COMPARISON")
    print("=" * 95)

    for strategy, r in results.items():
        print(
            f"{strategy}: "
            f"Top-1 {r['top1']}/{r['total']} "
            f"({pct(r['top1'], r['total']):.1f}%) | "
            f"Top-3 {r['top3']}/{r['total']} "
            f"({pct(r['top3'], r['total']):.1f}%)"
        )

    print()
    print("FOLLOW-UP CASES")

    for strategy, r in results.items():
        print(
            f"{strategy}: "
            f"Top-1 {r['follow_top1']}/{r['follow_total']} "
            f"({pct(r['follow_top1'], r['follow_total']):.1f}%) | "
            f"Top-3 {r['follow_top3']}/{r['follow_total']} "
            f"({pct(r['follow_top3'], r['follow_total']):.1f}%)"
        )

    print()
    print("STANDALONE CASES")

    for strategy, r in results.items():
        print(
            f"{strategy}: "
            f"Top-1 {r['standalone_top1']}/{r['standalone_total']} "
            f"({pct(r['standalone_top1'], r['standalone_total']):.1f}%) | "
            f"Top-3 {r['standalone_top3']}/{r['standalone_total']} "
            f"({pct(r['standalone_top3'], r['standalone_total']):.1f}%)"
        )

    baseline = results["CURRENT ONLY"]

    print()
    print("CHANGE VS CURRENT-QUESTION BASELINE")

    for strategy in strategies[1:]:
        r = results[strategy]

        print(
            f"{strategy}: "
            f"Top-1 {(r['top1'] - baseline['top1']) / baseline['total'] * 100:+.1f} pp | "
            f"Top-3 {(r['top3'] - baseline['top3']) / baseline['total'] * 100:+.1f} pp"
        )


if __name__ == "__main__":
    main()
