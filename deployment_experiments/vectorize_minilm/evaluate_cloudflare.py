import csv
import sys
from pathlib import Path

import requests

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Allow importing the frozen evaluation module and project config.
sys.path.insert(0, str(PROJECT_ROOT))

from Evaluation.evaluate_retrieval import (  # noqa: E402
    TEST_SET_TEXTBOOK,
    TEST_SET_CASUAL,
)

WORKER_URL = "https://wellness-ai-api.deswalgeetika.workers.dev/test/retrieve"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "deployment_experiments"
    / "vectorize_minilm"
    / "cloudflare_retrieval_results.csv"
)

questions = TEST_SET_TEXTBOOK + TEST_SET_CASUAL

print(f"Loaded {len(questions)} questions from frozen evaluation.")

rows = []

for i, (question, expected_source) in enumerate(questions, start=1):
    response = requests.post(
        WORKER_URL,
        json={"question": question},
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    matches = data.get("selected_matches", [])

    returned_ids = [m["id"] for m in matches]
    returned_sources = [
        m.get("metadata", {}).get("source_id")
        for m in matches
    ]

    top1_correct = (
        len(returned_sources) > 0
        and returned_sources[0] == expected_source
    )

    top3_correct = expected_source in returned_sources

    rows.append({
        "question_id": i,
        "question": question,
        "expected_source": expected_source,
        "rank1_id": returned_ids[0] if len(returned_ids) > 0 else "",
        "rank1_source": returned_sources[0] if len(returned_sources) > 0 else "",
        "rank2_id": returned_ids[1] if len(returned_ids) > 1 else "",
        "rank2_source": returned_sources[1] if len(returned_sources) > 1 else "",
        "rank3_id": returned_ids[2] if len(returned_ids) > 2 else "",
        "rank3_source": returned_sources[2] if len(returned_sources) > 2 else "",
        "top1_correct": top1_correct,
        "top3_correct": top3_correct,
    })

    status1 = "PASS" if top1_correct else "FAIL"
    status3 = "PASS" if top3_correct else "FAIL"

    print(
        f"[{i:02d}/{len(questions)}] "
        f"Top-1={status1} Top-3={status3} "
        f"| expected={expected_source} "
        f"| returned={returned_sources}"
    )

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

top1 = sum(row["top1_correct"] for row in rows)
top3 = sum(row["top3_correct"] for row in rows)

print()
print("=" * 50)
print("Cloudflare MiniLM + Vectorize Evaluation")
print("=" * 50)
print(f"Questions : {len(rows)}")
print(f"Top-1     : {top1}/{len(rows)} = {top1 / len(rows) * 100:.1f}%")
print(f"Top-3     : {top3}/{len(rows)} = {top3 / len(rows) * 100:.1f}%")
print(f"Output    : {OUTPUT_FILE}")
print("=" * 50)
