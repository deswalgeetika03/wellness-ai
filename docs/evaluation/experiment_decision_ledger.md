# Wellness AI â€” Experiment & Decision Ledger

## Purpose

This document records the major experiments and engineering decisions that shaped the final Wellness AI pipeline.

The project followed an experiment-driven development process. Candidate interventions were evaluated against defined measurements before being retained. Interventions that did not provide sufficient evidence of improvement were rejected, archived, or left unchanged.

The ledger preserves both successful and unsuccessful directions so that the final configuration can be understood in context.

---

## 1. Retrieval Experiments

### 1.1 Embedding Model Comparison

| Item | Decision |
|---|---|
| Area | Retrieval |
| Question | Would an alternative embedding model provide a meaningful improvement over the existing embedding model? |
| Baseline | `sentence-transformers/all-MiniLM-L6-v2` |
| Intervention | Evaluate BGE-based retrieval alternatives |
| Result | No sufficient improvement was demonstrated to justify migration |
| Decision | **Rejected** |
| Final choice | `sentence-transformers/all-MiniLM-L6-v2` |

The existing MiniLM configuration was retained because the alternative did not provide sufficient evidence of improvement relative to the additional complexity or change in the validated pipeline.

---

### 1.2 Candidate Pool and Top-K Evaluation

| Item | Decision |
|---|---|
| Area | Retrieval |
| Question | How many candidates should be retrieved before selecting the final context? |
| Intervention | Compare candidate-pool and final Top-K configurations |
| Result | A candidate pool of 10 with a final context of 3 provided the final retained configuration |
| Decision | **Retained** |
| Final configuration | Candidate pool = 10; final context = 3 |

The configuration balances retrieval coverage against unnecessary context expansion.

---

### 1.3 Source-Diversity Selection

| Item | Decision |
|---|---|
| Area | Retrieval |
| Question | Can source diversity improve the chance that useful evidence appears in the final context? |
| Baseline | Standard Top-3 selection |
| Intervention | Maximum 1 selected chunk per source |
| Result | Top-3 improved from **90.0% to 97.5%** |
| Top-1 effect | No change |
| Decision | **Retained** |

The source-diversity constraint was retained because it produced a measurable Top-3 improvement without increasing the final context size or changing Top-1 performance.

---

### 1.4 Heading-Aware Selection

| Item | Decision |
|---|---|
| Area | Retrieval |
| Question | Would heading-aware selection provide a reliable improvement in evidence retrieval? |
| Intervention | Use document heading information to influence retrieval/selection |
| Result | No sufficient improvement was demonstrated for the final configuration |
| Decision | **Rejected / not retained** |

The final system therefore uses the validated retrieval configuration rather than adding heading-aware selection without a measured benefit.

---

### 1.5 Query / Evidence Retrieval Interventions

| Item | Decision |
|---|---|
| Area | Retrieval / Evidence |
| Question | Could additional query or evidence-selection interventions materially improve retrieval quality? |
| Intervention | Evaluate alternative evidence/query-selection approaches |
| Result | No intervention provided sufficient evidence to replace the retained configuration |
| Decision | **Rejected / not retained** |

The project favored measured improvements over increasing pipeline complexity without a demonstrated benefit.

---

## 2. Generation and Grounding Experiments

### 2.1 Generation Interventions

| Item | Decision |
|---|---|
| Area | Generation |
| Question | Can generation behavior be improved while maintaining evidence grounding and safety constraints? |
| Intervention | Evaluate generation/prompting interventions |
| Historical baseline | **16/20 = 80%** |
| Final frozen result | **18/20 = 90%** |
| Decision | **Final configuration retained** |

The final configuration improved successful generation evaluations from 80% to 90%.

Two unsupported-claim failures remained in the final evaluation and were preserved as known limitations.

---

### 2.2 Evidence Extraction

| Item | Decision |
|---|---|
| Area | Evidence |
| Question | Can retrieved material be converted into a structured basis for response generation? |
| Intervention | Evidence extraction before final response generation |
| Result | Retained as part of the evidence-oriented generation pipeline |
| Decision | **Retained** |

Evidence extraction is used to provide a structured basis for supported claims rather than relying only on raw retrieved chunks.

---

### 2.3 Evidence Sufficiency / Gating

| Item | Decision |
|---|---|
| Area | Evidence / Safety |
| Question | What should happen when retrieved evidence is insufficient? |
| Intervention | Gate generation when sufficient supported evidence is unavailable |
| Result | Prevents the system from forcing unsupported responses |
| Decision | **Retained** |

The evidence gate is an intentional safety/grounding mechanism.

A known consequence is that some context-dependent follow-up questions can return:

```text
NO_SUPPORTED_EVIDENCE
```
---

### 2.4 Phase 7 Safety Revalidation

| Item | Decision |
|---|---|
| Area | Safety / Phase 5 revalidation |
| Finding | Restrictive-eating paraphrase was not detected by the deterministic safety layer |
| Discovery | Identified during the Phase 7 final release audit |
| Owning phase | **Phase 5 — Safety Evaluation** |
| Intervention | Expand deterministic restrictive-intent patterns and add regression coverage |
| Local result | **8/8 restrictive/eating detection PASS** |
| Production safety result | **17/17 PASS** |
| Full Worker result | **26/26 PASS** |
| Historical benchmark | **12/12 PASS retained unchanged** |
| Decision | **Resolved and re-frozen** |

The Phase 7 finding was outside the established frozen Phase 5 benchmark and therefore was not retroactively added to the original 12-case result.

The specific restrictive-eating coverage gap was resolved through implementation changes and regression testing. The original Phase 5 benchmark remains **12/12 PASS**, while the additional regression results are recorded separately.

Broader paraphrase and adversarial testing remains a future evaluation area; exhaustive coverage is not claimed.
