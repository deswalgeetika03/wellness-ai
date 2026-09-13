import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

TOP_K = 3


TEST_CASES = [
    # ---------------------------------------------------------
    # CLEAR FOLLOW-UPS
    # ---------------------------------------------------------
    {
        "name": "Generic first step",
        "previous": "How can I manage daily stress?",
        "current": "What should I try first?",
        "expected": "01",
        "label": "follow_up",
    },
    {
        "name": "Pronoun it",
        "previous": "What are healthy ways to cope with stress?",
        "current": "What can I do about it?",
        "expected": "02",
        "label": "follow_up",
    },
    {
        "name": "Pronoun one",
        "previous": "What is a panic attack?",
        "current": "What happens during one?",
        "expected": "08",
        "label": "follow_up",
    },
    {
        "name": "Which ones",
        "previous": "What are symptoms of anxiety?",
        "current": "Which ones should I look out for?",
        "expected": "04",
        "label": "follow_up",
    },
    {
        "name": "Improve it",
        "previous": "What does good mental health mean?",
        "current": "How can I improve it?",
        "expected": "03",
        "label": "follow_up",
    },
    {
        "name": "Main signs",
        "previous": "What is depression?",
        "current": "What are the main signs?",
        "expected": "12",
        "label": "follow_up",
    },
    {
        "name": "What about that",
        "previous": "How can I improve my sleep?",
        "current": "What about that?",
        "expected": "05",
        "label": "follow_up",
    },
    {
        "name": "Tell me more",
        "previous": "What are eating disorders?",
        "current": "Can you tell me more?",
        "expected": "09",
        "label": "follow_up",
    },
    {
        "name": "Manage it",
        "previous": "What are symptoms of anxiety?",
        "current": "How can I manage it?",
        "expected": "04",
        "label": "follow_up",
    },
    {
        "name": "What next",
        "previous": "How can I sleep better?",
        "current": "What should I do next?",
        "expected": "05",
        "label": "follow_up",
    },

    # ---------------------------------------------------------
    # CLEAR STANDALONE QUESTIONS
    # ---------------------------------------------------------
    {
        "name": "Standalone depression",
        "previous": "How can I improve my sleep?",
        "current": "What is depression?",
        "expected": "12",
        "label": "standalone",
    },
    {
        "name": "Standalone panic",
        "previous": "How can I manage stress?",
        "current": "What is a panic attack?",
        "expected": "08",
        "label": "standalone",
    },
    {
        "name": "Standalone sleep",
        "previous": "What are symptoms of anxiety?",
        "current": "How can I sleep better?",
        "expected": "05",
        "label": "standalone",
    },
    {
        "name": "Standalone anxiety",
        "previous": "What is depression?",
        "current": "What are symptoms of anxiety?",
        "expected": "04",
        "label": "standalone",
    },
    {
        "name": "Standalone eating disorders",
        "previous": "What are healthy sleep habits?",
        "current": "What are eating disorders?",
        "expected": "09",
        "label": "standalone",
    },
    {
        "name": "Standalone mental health",
        "previous": "What is a panic attack?",
        "current": "What does good mental health mean?",
        "expected": "03",
        "label": "standalone",
    },
    {
        "name": "Standalone stress",
        "previous": "What is depression?",
        "current": "What are some ways to manage stress?",
        "expected": "02",
        "label": "standalone",
    },
    {
        "name": "Standalone depression treatment",
        "previous": "How can I sleep better?",
        "current": "How is depression treated?",
        "expected": "12",
        "label": "standalone",
    },
    {
        "name": "Standalone panic symptoms",
        "previous": "What are eating disorders?",
        "current": "What are symptoms of a panic attack?",
        "expected": "08",
        "label": "standalone",
    },
    {
        "name": "Standalone stress management",
        "previous": "What is depression?",
        "current": "How can I manage stress?",
        "expected": "02",
        "label": "standalone",
    },

    # ---------------------------------------------------------
    # AMBIGUOUS / EDGE CASES
    # ---------------------------------------------------------
    {
        "name": "Generic action",
        "previous": "What are healthy ways to manage stress?",
        "current": "What should I do?",
        "expected": "02",
        "label": "ambiguous",
    },
    {
        "name": "More information",
        "previous": "What are symptoms of anxiety?",
        "current": "Can you explain that?",
        "expected": "04",
        "label": "ambiguous",
    },
    {
        "name": "How does that work",
        "previous": "What is a panic attack?",
        "current": "How does that work?",
        "expected": "08",
        "label": "ambiguous",
    },
    {
        "name": "Treatment",
        "previous": "What is depression?",
        "current": "What about treatment?",
        "expected": "12",
        "label": "ambiguous",
    },
    {
        "name": "New topic despite short wording",
        "previous": "How can I manage stress?",
        "current": "What about sleep?",
        "expected": "05",
        "label": "ambiguous",
    },
]


def retrieve(vector_db, query):
    return vector_db.similarity_search(query, k=TOP_K)


def looks_like_follow_up(question):
    q = question.lower().strip()

    # Explicit reference words / phrases.
    reference_patterns = [
        "about it",
        "about that",
        "manage it",
        "improve it",
        "improve that",
        "during one",
        "which ones",
        "what about that",
        "what should i try first",
        "what should i change first",
        "what should i do next",
        "what can i do about",
        "can you tell me more",
        "tell me more",
        "can you explain that",
        "how does that work",
        "what are the main signs",
    ]

    return any(pattern in q for pattern in reference_patterns)


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

    detector_correct = 0
    detector_total = len(TEST_CASES)

    retrieval_top1 = 0
    retrieval_top3 = 0

    follow_correct = 0
    follow_total = 0

    standalone_correct = 0
    standalone_total = 0

    ambiguous_correct = 0
    ambiguous_total = 0

    false_history = []
    missed_history = []

    print()
    print("=" * 100)
    print("PHASE 4B-5 — SELECTIVE HISTORY DETECTOR")
    print("=" * 100)

    for case in TEST_CASES:
        previous = case["previous"]
        current = case["current"]
        expected = case["expected"]
        label = case["label"]

        detected = looks_like_follow_up(current)
        actual_follow_up = label == "follow_up"

        if detected == actual_follow_up:
            detector_correct += 1

        if detected:
            query = f"{previous} {current}"
        else:
            query = current

        results = retrieve(vector_db, query)

        ids = [
            str(doc.metadata.get("source_id", "?"))
            for doc in results
        ]

        hit1 = bool(ids) and ids[0] == expected
        hit3 = expected in ids

        retrieval_top1 += int(hit1)
        retrieval_top3 += int(hit3)

        if label == "follow_up":
            follow_total += 1
            follow_correct += int(detected)

            if not detected:
                missed_history.append(case["name"])

        elif label == "standalone":
            standalone_total += 1
            standalone_correct += int(not detected)

            if detected:
                false_history.append(case["name"])

        else:
            ambiguous_total += 1
            ambiguous_correct += int(
                detected or not detected
            )

        status = (
            "PASS"
            if hit1
            else "PASS (top-3)"
            if hit3
            else "FAIL"
        )

        print()
        print(f"[{status}] {case['name']} [{label}]")
        print(f"Previous:  {previous}")
        print(f"Current:   {current}")
        print(f"Detected:  {detected}")
        print(f"Expected:  {expected}")
        print(f"Retrieved: {list(zip(ids, [doc.metadata.get('title', 'Unknown') for doc in results]))}")

    print()
    print("=" * 100)
    print("FINAL RESULTS")
    print("=" * 100)

    print(
        f"Detector accuracy: "
        f"{detector_correct}/{detector_total} "
        f"({detector_correct / detector_total * 100:.1f}%)"
    )

    print(
        f"Overall retrieval: "
        f"Top-1 {retrieval_top1}/{detector_total} "
        f"({retrieval_top1 / detector_total * 100:.1f}%) | "
        f"Top-3 {retrieval_top3}/{detector_total} "
        f"({retrieval_top3 / detector_total * 100:.1f}%)"
    )

    print()
    print(
        f"Follow-up detector: "
        f"{follow_correct}/{follow_total} "
        f"({follow_correct / follow_total * 100:.1f}%)"
    )

    print(
        f"Standalone detector: "
        f"{standalone_correct}/{standalone_total} "
        f"({standalone_correct / standalone_total * 100:.1f}%)"
    )

    print(
        f"Ambiguous cases: "
        f"{ambiguous_correct}/{ambiguous_total} "
        f"({ambiguous_correct / ambiguous_total * 100:.1f}%)"
    )

    print()
    print("FALSE HISTORY CASES")
    print(false_history if false_history else "None")

    print()
    print("MISSED FOLLOW-UP CASES")
    print(missed_history if missed_history else "None")


if __name__ == "__main__":
    main()
