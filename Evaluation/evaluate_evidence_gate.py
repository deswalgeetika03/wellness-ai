"""
Phase 6 — Evidence Sufficiency Gate Evaluator

TEMPORARY DIAGNOSTIC ONLY.
Does NOT modify production retrieval or query_pipeline.py.

Purpose:
- Measure whether retrieval distance can distinguish supported Wellness
  queries from clearly unsupported topics.
- Compare distance-only thresholds against a conservative
  distance + source-coherence rule.
"""

from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ============================================================
# TEST DATA
# ============================================================

queries = [

    # --------------------------------------------------------
    # CLEARLY UNSUPPORTED
    # Expected gate decision: REJECT
    # --------------------------------------------------------

    ("UNSUPPORTED", "What is the capital of France?"),
    ("UNSUPPORTED", "How does photosynthesis work?"),
    ("UNSUPPORTED", "Who invented the telephone?"),
    ("UNSUPPORTED", "What is the Python programming language?"),
    ("UNSUPPORTED", "How do black holes form?"),
    ("UNSUPPORTED", "What are the rules of cricket?"),

    # --------------------------------------------------------
    # NATURAL / EXPERIENTIAL WELLNESS
    # Expected gate decision: ACCEPT
    # --------------------------------------------------------

    ("WELLNESS", "I feel like my thoughts won't slow down and I can't settle myself."),
    ("WELLNESS", "Sometimes my heart suddenly races and I feel terrified."),
    ("WELLNESS", "I've been exhausted and don't enjoy things I normally like."),
    ("WELLNESS", "I keep waking up during the night and can't feel rested."),
    ("WELLNESS", "I feel overwhelmed and can't focus on anything."),
    ("WELLNESS", "I suddenly feel like something terrible is going to happen even when I'm safe."),

    # --------------------------------------------------------
    # CLEARLY SUPPORTED WELLNESS
    # Expected gate decision: ACCEPT
    # --------------------------------------------------------

    ("SUPPORTED", "What are symptoms of anxiety?"),
    ("SUPPORTED", "What is a panic attack?"),
    ("SUPPORTED", "What are symptoms of depression?"),
    ("SUPPORTED", "How can I improve my sleep?"),
    ("SUPPORTED", "How can I manage stress?"),
    ("SUPPORTED", "What are common eating disorders?"),
]


# ============================================================
# EXPECTED DECISIONS
# ============================================================

def expected_decision(category):
    """
    Unsupported topics should be rejected.
    Wellness and supported Wellness should be accepted.
    """
    return "REJECT" if category == "UNSUPPORTED" else "ACCEPT"


# ============================================================
# LOAD VECTOR DATABASE
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"local_files_only": True},
)

db = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=str(CHROMA_DIR),
    embedding_function=embeddings,
)


# ============================================================
# RETRIEVE DIAGNOSTIC DATA
# ============================================================

results_data = []

for category, query in queries:

    results = db.similarity_search_with_score(
        query,
        k=10,
    )

    top5 = results[:5]

    distances = [
        float(score)
        for _, score in top5
    ]

    sources = [
        doc.metadata.get("source_id", "UNKNOWN")
        for doc, _ in top5
    ]

    top1_distance = distances[0]
    top3_average = sum(distances[:3]) / 3
    top5_average = sum(distances) / len(distances)

    source_counts = {}

    for source in sources:
        source_counts[source] = source_counts.get(source, 0) + 1

    max_source_count = max(source_counts.values())

    # Fraction of top-5 results belonging to the most common source.
    source_coherence = max_source_count / len(sources)

    results_data.append({
        "category": category,
        "query": query,
        "top1": top1_distance,
        "top3_avg": top3_average,
        "top5_avg": top5_average,
        "source_coherence": source_coherence,
        "sources": sources,
    })


# ============================================================
# EVALUATION
# ============================================================

def evaluate_rule(name, decisions):

    total = len(results_data)

    correct = 0
    false_accepts = 0
    false_rejects = 0

    unsupported_total = 0
    unsupported_rejected = 0

    wellness_total = 0
    wellness_accepted = 0

    for row, predicted in zip(results_data, decisions):

        expected = expected_decision(row["category"])

        if expected == predicted:
            correct += 1

        if row["category"] == "UNSUPPORTED":

            unsupported_total += 1

            if predicted == "REJECT":
                unsupported_rejected += 1
            else:
                false_accepts += 1

        else:

            wellness_total += 1

            if predicted == "ACCEPT":
                wellness_accepted += 1
            else:
                false_rejects += 1

    accuracy = correct / total * 100

    unsupported_detection = (
        unsupported_rejected / unsupported_total * 100
    )

    wellness_retention = (
        wellness_accepted / wellness_total * 100
    )

    print("\n" + "=" * 100)
    print(name)
    print("=" * 100)

    print(f"Accuracy:              {accuracy:.1f}%")
    print(f"Unsupported detected:  {unsupported_detection:.1f}%")
    print(f"Wellness retained:     {wellness_retention:.1f}%")
    print(f"False accepts:         {false_accepts}")
    print(f"False rejects:         {false_rejects}")

    print("\nDecision details:")

    for row, predicted in zip(results_data, decisions):

        expected = expected_decision(row["category"])

        status = "PASS" if predicted == expected else "FAIL"

        print(
            f"{status:<5} "
            f"{row['category']:<11} "
            f"predicted={predicted:<6} "
            f"expected={expected:<6} "
            f"top1={row['top1']:.4f} "
            f"coherence={row['source_coherence']:.2f} "
            f"| {row['query']}"
        )

    return {
        "accuracy": accuracy,
        "unsupported_detection": unsupported_detection,
        "wellness_retention": wellness_retention,
        "false_accepts": false_accepts,
        "false_rejects": false_rejects,
    }


# ============================================================
# DISTANCE-ONLY RULES
# ============================================================

print("=" * 100)
print("PHASE 6 — EVIDENCE SUFFICIENCY GATE EVALUATION")
print("=" * 100)

print("\nDiagnostic data loaded.")
print(f"Queries: {len(results_data)}")
print("Production code modified: NO")


thresholds = [
    1.25,
    1.30,
    1.35,
    1.40,
    1.45,
    1.50,
]


summary = []


for threshold in thresholds:

    decisions = []

    for row in results_data:

        if row["top1"] > threshold:
            decisions.append("REJECT")
        else:
            decisions.append("ACCEPT")

    metrics = evaluate_rule(
        f"DISTANCE ONLY — threshold = {threshold:.2f}",
        decisions,
    )

    summary.append(
        (
            f"Distance {threshold:.2f}",
            metrics,
        )
    )


# ============================================================
# DISTANCE + SOURCE COHERENCE
# ============================================================

print("\n\n")
print("=" * 100)
print("COMBINATION RULES")
print("=" * 100)

print(
    """
Rule structure:

    REJECT when:
        top1 distance > threshold
        AND
        source coherence < minimum coherence

Otherwise:
    ACCEPT

This is intentionally conservative:
a weak retrieval result alone does not cause rejection.
"""
)


combination_thresholds = [
    1.25,
    1.30,
    1.35,
    1.40,
    1.45,
    1.50,
]

coherence_thresholds = [
    0.40,
    0.60,
    0.80,
]


for distance_threshold in combination_thresholds:

    for coherence_threshold in coherence_thresholds:

        decisions = []

        for row in results_data:

            reject = (
                row["top1"] > distance_threshold
                and
                row["source_coherence"] < coherence_threshold
            )

            if reject:
                decisions.append("REJECT")
            else:
                decisions.append("ACCEPT")

        metrics = evaluate_rule(
            (
                f"COMBINATION — "
                f"distance > {distance_threshold:.2f} "
                f"AND coherence < {coherence_threshold:.2f}"
            ),
            decisions,
        )

        summary.append(
            (
                (
                    f"Combo "
                    f"{distance_threshold:.2f}/"
                    f"{coherence_threshold:.2f}"
                ),
                metrics,
            )
        )


# ============================================================
# SUMMARY TABLE
# ============================================================

print("\n\n")
print("=" * 100)
print("FINAL COMPARISON")
print("=" * 100)

print(
    f"{'Rule':<30}"
    f"{'Accuracy':>12}"
    f"{'Unsupported':>15}"
    f"{'Wellness':>12}"
    f"{'False Accept':>15}"
    f"{'False Reject':>15}"
)

print("-" * 100)

for name, metrics in summary:

    print(
        f"{name:<30}"
        f"{metrics['accuracy']:>11.1f}%"
        f"{metrics['unsupported_detection']:>14.1f}%"
        f"{metrics['wellness_retention']:>11.1f}%"
        f"{metrics['false_accepts']:>15}"
        f"{metrics['false_rejects']:>15}"
    )


# ============================================================
# SAFEST CANDIDATES
# ============================================================

print("\n\n")
print("=" * 100)
print("INTERPRETATION")
print("=" * 100)

print(
    """
Important:

This script is diagnostic only.

DO NOT copy any threshold into query_pipeline.py yet.

The preferred production candidate should:

1. Reject as many clearly unsupported questions as possible.
2. Avoid rejecting natural Wellness experiences.
3. Avoid rejecting clearly supported Wellness questions.
4. Prefer false accepts over false rejects when the evidence is uncertain,
   because a conservative Wellness assistant should not unnecessarily
   block a legitimate user seeking help.

Review the numbers above before making any production change.
"""
)

print("\nDiagnostic complete.")