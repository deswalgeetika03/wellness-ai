"""
test_mmr_retrieval.py

Compares MMR (Maximal Marginal Relevance) retrieval against the
existing similarity-search baseline.

Uses the EXACT SAME 40 questions and expected source IDs as
evaluate_retrieval.py so the comparison is fair.

Metrics:
    - Top-1 accuracy
    - Top-3 accuracy

Usage:
    python test_mmr_retrieval.py
"""

import csv
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

from rag_config import CHROMA_DIR, COLLECTION_NAME

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 3

# MMR fetches more candidates first, then selects diverse results.
FETCH_K = 12

LAMBDA_MULT = 0.5

OUTPUT_DIR = Path("data/eval")

OUTPUT_CSV = OUTPUT_DIR / "mmr_retrieval_eval_results.csv"


# ------------------------------------------------------------
# Test Set A — Textbook phrasing
# ------------------------------------------------------------

TEST_SET_TEXTBOOK = [

    # Stress
    ("How can I manage daily stress?", "01"),
    ("What can I do when I feel overwhelmed?", "01"),
    ("What are healthy ways to cope with stress?", "02"),

    # Anxiety
    ("What are symptoms of anxiety?", "04"),
    ("Why do I feel constantly worried?", "04"),
    ("What are anxiety disorders?", "04"),

    # Panic
    ("What is a panic attack?", "08"),
    ("Why do panic attacks happen?", "08"),
    ("How is panic disorder treated?", "08"),

    # Sleep
    ("How can I sleep better?", "05"),
    ("What habits improve sleep?", "05"),
    ("Why should I avoid caffeine before bed?", "05"),

    # Eating disorders
    ("What are eating disorders?", "09"),
    ("What are common types of eating disorders?", "09"),
    ("Where can someone with an eating disorder get help?", "09"),

    # Depression
    ("What is depression?", "12"),
    ("What are symptoms of depression?", "12"),
    ("How is depression treated?", "12"),

    # General mental health
    ("What does it mean to have good mental health?", "03"),
    ("What are common mental disorders?", "10"),
]


# ------------------------------------------------------------
# Test Set B — Casual / emotional phrasing
# ------------------------------------------------------------

TEST_SET_CASUAL = [

    # Stress
    ("i have so much to do and i dont know where to start", "01"),
    ("everything feels like too much right now", "01"),
    ("how do i chill out after a rough day", "02"),

    # Anxiety
    ("why do i feel nervous and on edge all the time", "04"),
    ("my mind wont stop racing with worry", "04"),
    ("is it normal to worry about everything", "04"),

    # Panic
    ("my heart was pounding and i couldnt breathe, what was that", "08"),
    ("i felt like i was dying but the doctor said i was fine", "08"),
    ("how do you stop a panic attack once it starts", "08"),

    # Sleep
    ("i cant fall asleep no matter what i try", "05"),
    ("why am i so tired even after sleeping 8 hours", "05"),
    ("does scrolling my phone in bed mess up my sleep", "05"),

    # Eating disorders
    ("i cant stop thinking about food and calories", "09"),
    ("my friend barely eats anything, should i be worried", "09"),
    ("is it normal to binge eat when stressed", "09"),

    # Depression
    ("i just feel empty and dont enjoy anything anymore", "12"),
    ("why do i feel sad for no reason", "12"),
    ("can therapy actually help with feeling low all the time", "12"),

    # General mental health
    ("what does being mentally healthy even mean", "03"),
    ("what kinds of mental health problems are common in students", "10"),
]


# ------------------------------------------------------------
# Run one evaluation batch
# ------------------------------------------------------------

def run_batch(vector_db, test_set, batch_name):

    rows = []
    top1_hits = 0
    top3_hits = 0

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": TOP_K,
            "fetch_k": FETCH_K,
            "lambda_mult": LAMBDA_MULT,
        },
    )

    print()
    print("-" * 60)
    print(
        f"MMR Batch: {batch_name} "
        f"({len(test_set)} questions)"
    )
    print("-" * 60)

    for question, expected_id in test_set:

        retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={
        "k": TOP_K,
        "fetch_k": FETCH_K,
        "lambda_mult": LAMBDA_MULT,
    },
)

        results = retriever.invoke(question)

        retrieved_ids = [
            document.metadata.get("source_id")
            for document in results
        ]

        retrieved_titles = [
            document.metadata.get("title")
            for document in results
        ]

        top1_success = (
            len(retrieved_ids) > 0
            and retrieved_ids[0] == expected_id
        )

        top3_success = expected_id in retrieved_ids

        top1_hits += int(top1_success)
        top3_hits += int(top3_success)

        if top1_success:

            status = "PASS (top-1)"

        elif top3_success:

            status = "PASS (top-3 only)"

        else:

            status = "FAIL"

        print(f"[{status}] {question}")

        print(
            f"       expected source_id={expected_id}"
        )

        print(
            f"       got: "
            f"{list(zip(retrieved_ids, retrieved_titles))}"
        )

        print()

        rows.append(
            {
                "batch": batch_name,
                "question": question,
                "expected_source_id": expected_id,
                "retrieved_source_ids": ";".join(
                    retrieved_ids
                ),
                "retrieved_titles": ";".join(
                    retrieved_titles
                ),
                "top1_success": top1_success,
                "top3_success": top3_success,
            }
        )

    return rows, top1_hits, top3_hits


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 60)
    print("WELLNESS RAG — MMR RETRIEVAL TEST")
    print("=" * 60)

    print()
    print("Embedding model:")
    print(EMBEDDING_MODEL)

    print()
    print("MMR configuration:")
    print(f"Top-K:       {TOP_K}")
    print(f"Fetch-K:     {FETCH_K}")
    print(f"Lambda:      {LAMBDA_MULT}")

    print()
    print("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print("Embedding model loaded.")

    print()
    print("Connecting to ChromaDB...")

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    print("ChromaDB connected.")

    # --------------------------------------------------------
    # Run both batches
    # --------------------------------------------------------

    textbook_rows, tb_top1, tb_top3 = run_batch(
        vector_db,
        TEST_SET_TEXTBOOK,
        "textbook",
    )

    casual_rows, cs_top1, cs_top3 = run_batch(
        vector_db,
        TEST_SET_CASUAL,
        "casual",
    )

    all_rows = textbook_rows + casual_rows

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=all_rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(all_rows)

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    def percentage(hits, total):

        return hits / total * 100

    n_textbook = len(TEST_SET_TEXTBOOK)
    n_casual = len(TEST_SET_CASUAL)

    total_questions = n_textbook + n_casual

    all_top1 = tb_top1 + cs_top1
    all_top3 = tb_top3 + cs_top3

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("=" * 60)
    print("MMR SUMMARY")
    print("=" * 60)

    print(
        f"{'Batch':<12}"
        f"{'Top-1':<18}"
        f"{'Top-3':<18}"
    )

    print(
        f"{'Textbook':<12}"
        f"{tb_top1}/{n_textbook} "
        f"({percentage(tb_top1, n_textbook):.1f}%)"
        f"{'':<6}"
        f"{tb_top3}/{n_textbook} "
        f"({percentage(tb_top3, n_textbook):.1f}%)"
    )

    print(
        f"{'Casual':<12}"
        f"{cs_top1}/{n_casual} "
        f"({percentage(cs_top1, n_casual):.1f}%)"
        f"{'':<6}"
        f"{cs_top3}/{n_casual} "
        f"({percentage(cs_top3, n_casual):.1f}%)"
    )

    print(
        f"{'Overall':<12}"
        f"{all_top1}/{total_questions} "
        f"({percentage(all_top1, total_questions):.1f}%)"
        f"{'':<6}"
        f"{all_top3}/{total_questions} "
        f"({percentage(all_top3, total_questions):.1f}%)"
    )

    print()
    print(f"Results saved to: {OUTPUT_CSV}")

    # --------------------------------------------------------
    # Show failures
    # --------------------------------------------------------

    failures = [
        row
        for row in all_rows
        if not row["top3_success"]
    ]

    top1_misses = [
        row
        for row in all_rows
        if (
            row["top3_success"]
            and not row["top1_success"]
        )
    ]

    if failures:

        print()
        print(
            "Full failures "
            "(correct source missing from top-3):"
        )

        for row in failures:

            print(
                f"  - [{row['batch']}] "
                f"{row['question']} "
                f"(expected "
                f"{row['expected_source_id']})"
            )

    if top1_misses:

        print()
        print(
            "Top-1 misses "
            "(correct source present, "
            "but not ranked first):"
        )

        for row in top1_misses:

            print(
                f"  - [{row['batch']}] "
                f"{row['question']} "
                f"(expected "
                f"{row['expected_source_id']})"
            )

    print()
    print("=" * 60)
    print("MMR RETRIEVAL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()