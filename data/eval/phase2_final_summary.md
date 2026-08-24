# Phase 2 — Answer Quality + Safety Evaluation

## Evaluation Set

20 fixed questions were evaluated using the Wellness RAG pipeline.

The retrieval system and safety architecture were kept unchanged during
the generation-quality evaluation.

## Baseline — Before Prompt Intervention

| Metric | Result |
|---|---:|
| Route accuracy | 20/20 (100%) |
| Diagnostic safety | 19/20 (95%) |
| Grounding | 12/16 (75%) |
| Tone | 14/16 (87.5%) |
| Overall acceptable | 16/20 (80%) |

## Prompt Intervention

Three targeted generation instructions were added:

1. Do not attach a named mental-health disorder to the user's personal
   symptoms.
2. Keep factual and medical claims grounded in the retrieved context.
3. Avoid broad unsupported normalizing or reassuring statements.

The same 20-question evaluation set was then run again.

## After Prompt Intervention

| Metric | Result |
|---|---:|
| Route accuracy | 20/20 (100%) |
| Diagnostic safety | 19/20 (95%) |
| Grounding | 12/16 (75%) |
| Tone | 18/20 (90%) |
| Overall acceptable | 16/20 (80%) |

## Findings

The intervention preserved the existing safety-routing behavior and
produced a modest improvement in tone.

However, diagnostic safety, grounding, and overall pass rate did not
improve on the fixed evaluation set.

## Known Limitations

Residual failures included:

- personalized diagnostic framing in a panic-related response;
- unsupported or overly broad reassuring statements;
- additional factual/clinical details not present in retrieved context.

Prompt-only controls were therefore not sufficient to eliminate all
generation-level failures in the tested cases.

## Decision

Further prompt optimization was not pursued. The remaining limitations
are documented as part of the Responsible AI evaluation rather than
continuing uncontrolled prompt iteration.

## Evidence Artifacts

- `generation_eval.csv`
- `generation_baseline.csv`
- `retrieved_chunks.json`
- `generation_after.csv`
- `retrieved_chunks_after.json`
- `generation_after_graded.csv`