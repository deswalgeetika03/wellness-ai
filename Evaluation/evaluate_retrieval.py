"""
evaluate_retrieval.py

Controlled retrieval experiment for the Wellness RAG system.

Compares:
1. Plain similarity search
2. Source-diversity-capped retrieval

Both methods use the exact same 40-question evaluation set.

The source-diversity method retrieves a wider candidate pool and then
selects the best 3 while limiting repeated chunks from the same source.
This specifically tests whether Source 01's large chunk count is causing
retrieval bias.

Usage:
    python evaluate_retrieval.py
"""

import csv
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

TOP_K = 3
CANDIDATE_K = 10

# Maximum number of chunks from one source in the final result.
MAX_PER_SOURCE = 1

OUTPUT_DIR = Path("data/eval")
OUTPUT_CSV = OUTPUT_DIR / "retrieval_diversity_eval_results.csv"


# ---------------------------------------------------------------------
# Test set A: textbook phrasing
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Test set B: casual / emotional phrasing
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Plain similarity retrieval
# ---------------------------------------------------------------------

def retrieve_plain(vector_db, question):
    """
    Standard similarity search.

    Returns the top TOP_K chunks exactly as the normal RAG system would
    retrieve them.
    """

    return vector_db.similarity_search(
        question,
        k=TOP_K,
    )


# ---------------------------------------------------------------------
# Source-diversity retrieval
# ---------------------------------------------------------------------

def retrieve_source_diverse(vector_db, question):
    """
    Retrieve a wider candidate pool and limit repeated sources.

    Example:

        Candidate pool:
        01, 01, 01, 04, 01, 06, 04, 10, 01, 04

    With MAX_PER_SOURCE = 1, final result becomes approximately:

        01, 04, 06

    This directly tests whether Source 01 is dominating because it
    contributes 42.9% of the database chunks.
    """

    candidates = vector_db.similarity_search(
        question,
        k=CANDIDATE_K,
    )

    selected = []
    source_counts = {}

    # First pass: enforce the source cap.
    for doc in candidates:
        source_id = str(doc.metadata.get("source_id", "?"))

        count = source_counts.get(source_id, 0)

        if count >= MAX_PER_SOURCE:
            continue

        selected.append(doc)
        source_counts[source_id] = count + 1

        if len(selected) >= TOP_K:
            break

    # Safety fallback:
    # If fewer than TOP_K unique sources exist in the candidate pool,
    # fill remaining positions with the best remaining candidates.
    if len(selected) < TOP_K:

        selected_ids = {
            id(doc)
            for doc in selected
        }

        for doc in candidates:

            if id(doc) in selected_ids:
                continue

            selected.append(doc)

            if len(selected) >= TOP_K:
                break

    return selected


# ---------------------------------------------------------------------
# Run one evaluation batch
# ---------------------------------------------------------------------

def run_batch(
    vector_db,
    test_set,
    batch_name,
    retrieval_function,
    strategy_name,
):

    rows = []

    top1_hits = 0
    top3_hits = 0

    print()
    print("-" * 70)
    print(
        f"{strategy_name} | {batch_name} "
        f"({len(test_set)} questions)"
    )
    print("-" * 70)
    print()

    for question, expected_id in test_set:

        results = retrieval_function(
            vector_db,
            question,
        )

        retrieved_ids = [
            str(doc.metadata.get("source_id", "?"))
            for doc in results
        ]

        retrieved_titles = [
            doc.metadata.get(
                "title",
                "Unknown source"
            )
            for doc in results
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

        rows.append({
            "strategy": strategy_name,
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
        })

    return rows, top1_hits, top3_hits


# ---------------------------------------------------------------------
# Diagnostic pass
# ---------------------------------------------------------------------

KNOWN_FAILURES = [
    (
        "my mind wont stop racing with worry",
        "04",
    ),
    (
        "my heart was pounding and i couldnt breathe, what was that",
        "08",
    ),
    (
        "i felt like i was dying but the doctor said i was fine",
        "08",
    ),
    (
        "i just feel empty and dont enjoy anything anymore",
        "12",
    ),
]


def diagnostic_candidate_pool(vector_db):

    print()
    print("=" * 70)
    print("DIAGNOSTIC: TOP-10 CANDIDATE POOL")
    print("=" * 70)

    for question, expected_id in KNOWN_FAILURES:

        candidates = vector_db.similarity_search(
            question,
            k=CANDIDATE_K,
        )

        print()
        print(f"Question: {question}")
        print(f"Expected source: {expected_id}")
        print("-" * 70)

        for rank, doc in enumerate(
            candidates,
            start=1,
        ):

            source_id = doc.metadata.get(
                "source_id",
                "?",
            )

            title = doc.metadata.get(
                "title",
                "Unknown",
            )

            preview = (
                doc.page_content
                .replace("\n", " ")
                [:100]
            )

            marker = (
                " <-- EXPECTED"
                if str(source_id) == expected_id
                else ""
            )

            print(
                f"{rank:>2}. "
                f"source={source_id} | "
                f"{title} | "
                f"{preview}{marker}"
            )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("WELLNESS RAG — SOURCE DIVERSITY RETRIEVAL EXPERIMENT")
    print("=" * 70)

    print()
    print("Embedding model:")
    print(EMBEDDING_MODEL)

    print()
    print("Retrieval configuration:")
    print(f"Normal Top-K:       {TOP_K}")
    print(f"Candidate pool:     {CANDIDATE_K}")
    print(f"Max per source:     {MAX_PER_SOURCE}")

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
        persist_directory=str(CHROMA_DIR),
    )

    print("ChromaDB connected.")

    # -------------------------------------------------------------
    # Baseline
    # -------------------------------------------------------------

    tb_plain_rows, tb_plain_top1, tb_plain_top3 = run_batch(
        vector_db,
        TEST_SET_TEXTBOOK,
        "textbook",
        retrieve_plain,
        "PLAIN SIMILARITY",
    )

    cs_plain_rows, cs_plain_top1, cs_plain_top3 = run_batch(
        vector_db,
        TEST_SET_CASUAL,
        "casual",
        retrieve_plain,
        "PLAIN SIMILARITY",
    )

    # -------------------------------------------------------------
    # Source-diversity experiment
    # -------------------------------------------------------------

    tb_div_rows, tb_div_top1, tb_div_top3 = run_batch(
        vector_db,
        TEST_SET_TEXTBOOK,
        "textbook",
        retrieve_source_diverse,
        "SOURCE-DIVERSITY",
    )

    cs_div_rows, cs_div_top1, cs_div_top3 = run_batch(
        vector_db,
        TEST_SET_CASUAL,
        "casual",
        retrieve_source_diverse,
        "SOURCE-DIVERSITY",
    )

    # -------------------------------------------------------------
    # Save CSV
    # -------------------------------------------------------------

    all_rows = (
        tb_plain_rows
        + cs_plain_rows
        + tb_div_rows
        + cs_div_rows
    )

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

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    def pct(hits, total):
        return hits / total * 100

    n_tb = len(TEST_SET_TEXTBOOK)
    n_cs = len(TEST_SET_CASUAL)
    n_all = n_tb + n_cs

    plain_top1 = (
        tb_plain_top1
        + cs_plain_top1
    )

    plain_top3 = (
        tb_plain_top3
        + cs_plain_top3
    )

    div_top1 = (
        tb_div_top1
        + cs_div_top1
    )

    div_top3 = (
        tb_div_top3
        + cs_div_top3
    )

    print()
    print("=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    print()
    print(
        f"{'Strategy':<22}"
        f"{'Batch':<12}"
        f"{'Top-1':<18}"
        f"{'Top-3':<18}"
    )

    print(
        f"{'Plain similarity':<22}"
        f"{'Textbook':<12}"
        f"{tb_plain_top1}/{n_tb} "
        f"({pct(tb_plain_top1, n_tb):.1f}%)"
        f"{'':<4}"
        f"{tb_plain_top3}/{n_tb} "
        f"({pct(tb_plain_top3, n_tb):.1f}%)"
    )

    print(
        f"{'Plain similarity':<22}"
        f"{'Casual':<12}"
        f"{cs_plain_top1}/{n_cs} "
        f"({pct(cs_plain_top1, n_cs):.1f}%)"
        f"{'':<4}"
        f"{cs_plain_top3}/{n_cs} "
        f"({pct(cs_plain_top3, n_cs):.1f}%)"
    )

    print(
        f"{'Source-diversity':<22}"
        f"{'Textbook':<12}"
        f"{tb_div_top1}/{n_tb} "
        f"({pct(tb_div_top1, n_tb):.1f}%)"
        f"{'':<4}"
        f"{tb_div_top3}/{n_tb} "
        f"({pct(tb_div_top3, n_tb):.1f}%)"
    )

    print(
        f"{'Source-diversity':<22}"
        f"{'Casual':<12}"
        f"{cs_div_top1}/{n_cs} "
        f"({pct(cs_div_top1, n_cs):.1f}%)"
        f"{'':<4}"
        f"{cs_div_top3}/{n_cs} "
        f"({pct(cs_div_top3, n_cs):.1f}%)"
    )

    print()
    print("-" * 70)

    print(
        f"{'Overall plain':<22}"
        f"{plain_top1}/{n_all} "
        f"({pct(plain_top1, n_all):.1f}%)"
        f"{'':<8}"
        f"{plain_top3}/{n_all} "
        f"({pct(plain_top3, n_all):.1f}%)"
    )

    print(
        f"{'Overall diversity':<22}"
        f"{div_top1}/{n_all} "
        f"({pct(div_top1, n_all):.1f}%)"
        f"{'':<8}"
        f"{div_top3}/{n_all} "
        f"({pct(div_top3, n_all):.1f}%)"
    )

    # -------------------------------------------------------------
    # Difference
    # -------------------------------------------------------------

    top1_change = (
        pct(div_top1, n_all)
        - pct(plain_top1, n_all)
    )

    top3_change = (
        pct(div_top3, n_all)
        - pct(plain_top3, n_all)
    )

    print()
    print("CHANGE FROM BASELINE")
    print("-" * 70)

    print(
        f"Top-1 change: "
        f"{top1_change:+.1f} percentage points"
    )

    print(
        f"Top-3 change: "
        f"{top3_change:+.1f} percentage points"
    )

    print()
    print(f"Results saved to: {OUTPUT_CSV}")

    # -------------------------------------------------------------
    # Diagnostic candidate pool
    # -------------------------------------------------------------

    diagnostic_candidate_pool(vector_db)

    print()
    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()