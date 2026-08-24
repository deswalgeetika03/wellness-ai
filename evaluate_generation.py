"""
evaluate_generation.py

Phase 2B — Granite answer-quality baseline evaluation.

Runs the fixed evaluation set through the real Wellness RAG pipeline.

Outputs:
    data/eval/generation_baseline.csv
    data/eval/retrieved_chunks.json
"""

import csv
import json
from pathlib import Path

from query_pipeline import get_vector_db, answer_query


# ============================================================
# CONFIGURATION
# ============================================================

EVAL_FILE = Path("data/eval/generation_eval.csv")
OUTPUT_FILE = Path("data/eval/generation_after.csv")
CHUNKS_FILE = Path("data/eval/retrieved_chunks_after.json")


GRADING_COLUMNS = [
    "diagnostic_label",
    "unsupported_claim",
    "grounded",
    "tone_appropriate",
    "overall",
    "notes",
]


# ============================================================
# REQUIRED STRUCTURE
# ============================================================

REQUIRED_SOURCE_KEYS = {
    "organization",
    "title",
}

REQUIRED_CHUNK_KEYS = {
    "source_id",
    "organization",
    "title",
    "text",
}


# ============================================================
# LOAD QUESTIONS
# ============================================================

def load_questions():

    if not EVAL_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation file not found: {EVAL_FILE}"
        )

    with EVAL_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "id",
            "category",
            "question",
            "expected_route",
        }

        missing = required_columns - set(reader.fieldnames or [])

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing))
            )

        questions = list(reader)

    if not questions:
        raise ValueError(
            "The evaluation file contains no questions."
        )

    return questions


# ============================================================
# FORMAT SOURCES
# ============================================================

def format_sources(sources):

    formatted = []

    for source in sources:

        missing = REQUIRED_SOURCE_KEYS - set(source.keys())

        if missing:
            raise ValueError(
                f"Source is missing keys: "
                f"{sorted(missing)}"
            )

        formatted.append({
            "organization": source["organization"],
            "title": source["title"],
        })

    return formatted


# ============================================================
# FORMAT RETRIEVED CHUNKS
# ============================================================

def format_chunks(chunks):

    formatted = []

    for chunk in chunks:

        missing = REQUIRED_CHUNK_KEYS - set(chunk.keys())

        if missing:
            raise ValueError(
                f"Retrieved chunk is missing keys: "
                f"{sorted(missing)}"
            )

        formatted.append({
            "source_id": chunk["source_id"],
            "organization": chunk["organization"],
            "title": chunk["title"],
            "text": chunk["text"],
        })

    return formatted


# ============================================================
# RUN BASELINE
# ============================================================

def run_evaluation():

    questions = load_questions()

    print("=" * 70)
    print("WELLNESS RAG — PHASE 2B GENERATION BASELINE")
    print("=" * 70)

    print(f"\nEvaluation questions: {len(questions)}")
    print(f"Input:  {EVAL_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Chunks: {CHUNKS_FILE}")

    print("\nLoading vector database...")

    vector_db = get_vector_db()

    print("Vector database ready.")
    print("\nRunning baseline evaluation...\n")

    results = []
    retrieved_chunks = {}

    passed_routes = 0

    for number, test_case in enumerate(
        questions,
        start=1,
    ):

        question_id = test_case["id"]
        category = test_case["category"]
        question = test_case["question"]
        expected_route = test_case["expected_route"]

        print("-" * 70)
        print(f"QUESTION {number}/{len(questions)}")
        print(f"ID:       {question_id}")
        print(f"Category: {category}")
        print(f"Question: {question}")
        print(f"Expected: {expected_route}")

        try:

            result = answer_query(
                vector_db,
                question,
            )

            actual_route = result["route"]
            answer = result["answer"]

            sources = format_sources(
                result.get("sources", [])
            )

            chunks = format_chunks(
                result.get("context_chunks", [])
            )

            route_pass = (
                actual_route == expected_route
            )

            if route_pass:
                passed_routes += 1

            retrieved_chunks[question_id] = {
                "id": question_id,
                "category": category,
                "question": question,
                "route": actual_route,
                "chunks": chunks,
            }

            result_row = {
                "id": question_id,
                "category": category,
                "question": question,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "retrieved_sources": json.dumps(
                    sources,
                    ensure_ascii=False,
                ),
                "answer": answer,
            }

            for column in GRADING_COLUMNS:
                result_row[column] = ""

            results.append(result_row)

            print(f"Actual:   {actual_route}")

            if route_pass:
                print("Route:    PASS")
            else:
                print("Route:    FAIL")

            print(f"Sources:  {len(sources)}")

            print("\nAnswer:")
            print(answer)

        except Exception as error:

            print("\nERROR:")
            print(
                f"{type(error).__name__}: {error}"
            )

            result_row = {
                "id": question_id,
                "category": category,
                "question": question,
                "expected_route": expected_route,
                "actual_route": "ERROR",
                "retrieved_sources": "[]",
                "answer": "",
            }

            for column in GRADING_COLUMNS:
                result_row[column] = ""

            result_row["notes"] = (
                f"{type(error).__name__}: {error}"
            )

            results.append(result_row)

            retrieved_chunks[question_id] = {
                "id": question_id,
                "category": category,
                "question": question,
                "route": "ERROR",
                "chunks": [],
            }

    # ========================================================
    # WRITE CSV
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "id",
        "category",
        "question",
        "expected_route",
        "actual_route",
        "retrieved_sources",
        "answer",
        *GRADING_COLUMNS,
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    # ========================================================
    # WRITE FULL RETRIEVED CONTEXT
    # ========================================================

    with CHUNKS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            retrieved_chunks,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(results)
    route_failed = total - passed_routes

    print("\n" + "=" * 70)
    print("BASELINE SUMMARY")
    print("=" * 70)

    print(f"Total questions:  {total}")
    print(f"Routes correct:   {passed_routes}")
    print(f"Routes incorrect: {route_failed}")

    if total:
        print(
            f"Route accuracy:   "
            f"{passed_routes / total * 100:.1f}%"
        )

    print("\nFiles written:")
    print(f"  {OUTPUT_FILE}")
    print(f"  {CHUNKS_FILE}")

    print("\nHuman grading columns remain blank.")
    print("Do not modify the answers before grading.")

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_evaluation()