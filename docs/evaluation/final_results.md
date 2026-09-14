# Wellness AI — Final Evaluation Results

## Overview

This document consolidates the final frozen evaluation results for Wellness AI across retrieval, safety, generation, grounding, conversational behavior, and production end-to-end validation.

The results represent internal prototype engineering evaluations conducted during the project's evaluation phases. They are intended to measure system behavior, compare design decisions, identify regressions, and document known limitations.

These results do not represent clinical validation, medical accuracy certification, or real-world health outcomes.

---

## 1. Retrieval Evaluation

The retrieval system was evaluated using a 40-question benchmark:

- 20 textbook-style questions
- 20 casual/user-style questions

### Final Configuration

| Configuration | Final value |
|---|---|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector database | ChromaDB locally / Cloudflare Vectorize in production |
| Candidate pool | 10 |
| Final context | 3 chunks |
| Maximum chunks per source | 1 |
| Similarity metric | Cosine |

### Final Results

| Metric | Result |
|---|---:|
| Top-1 retrieval | **67.5%** |
| Top-3 retrieval | **97.5%** |

The source-diversity constraint improved Top-3 retrieval from **90.0% to 97.5%** without changing Top-1 performance.

The final configuration was retained because it improved evidence coverage while keeping the final context limited to three chunks.

### Breakdown

| Benchmark subset | Top-1 | Top-3 |
|---|---:|---:|
| Textbook | 75.0% | 100% |
| Casual | 60.0% | 80.0% |
| Overall | **67.5%** | **97.5%** |

---

## 2. Safety Evaluation

The system uses deterministic safety routing for sensitive scenarios before normal retrieval and generation.

The final local deterministic safety suite achieved:

**12/12 PASS**

Production validation additionally covered:

- Crisis-related scenarios
- Medication-related restricted scenarios
- Restrictive/eating-related scenarios
- Normal well-being queries
- Unsupported requests
- Topic switching
- Conversation-history interactions

The safety architecture prioritizes the current user question so that unrelated historical context does not override the current safety intent.

### Safety Revalidation

The **12/12 PASS** result remains the historical frozen Phase 5 deterministic safety benchmark. It was not retroactively changed when additional coverage was added.

During the Phase 7 release audit, an exploratory restrictive-eating paraphrase was identified outside the established benchmark. The safety implementation was updated to cover the missed restrictive-intent patterns.

The fix was revalidated with additional regression coverage:

- Local restrictive/eating detection: **8/8 PASS**
- Production safety test suite: **17/17 PASS**
- Full Cloudflare Worker test suite: **26/26 PASS**

**Status: RESOLVED and re-frozen.**

This resolves the specific restrictive-eating coverage gap identified during Phase 7. Broader paraphrase and adversarial testing remains a general future evaluation area and is not claimed to be exhaustive.

---

## 3. Generation Evaluation

Generation was evaluated using a 20-case evaluation set.

### Final Result

**18/20 successful evaluations — 90%**

For historical comparison, an earlier generation baseline achieved:

**16/20 — 80%**

The final evaluation therefore represents an improvement of **10 percentage points** over the historical baseline.

Two final-generation evaluations contained unsupported claims. These cases were retained in the evaluation record and are documented as known limitations.

---

## 4. Grounding Evaluation

Grounding was evaluated separately from overall generation success.

Among the applicable grounding cases:

**15/16 were grounded — 93.75%**

This is the appropriate grounding metric because three cases in the full 20-case set were safety or otherwise non-applicable cases.

### Grounding Summary

| Category | Result |
|---|---:|
| Applicable grounding cases | 16 |
| Grounded cases | 15 |
| Applicable grounding | **93.75%** |
| Unsupported-claim failures | 2 |
| Safety / non-applicable cases | 3 |

The two unsupported-claim failures remain part of the final evaluation record.

The project does **not** report 15/20 as the final grounding accuracy because the denominator includes safety/non-applicable cases.

---

## 5. Response Quality Checks

The final generation evaluation also included qualitative response checks.

| Check | Result |
|---|---:|
| Appropriate tone | **20/20** |
| Diagnostic-label avoidance | **20/20** |

These checks were used alongside grounding and generation evaluation rather than being treated as substitutes for factual or evidence-based evaluation.

---

## 6. Follow-Up Detection

The follow-up detector was evaluated for context-dependent and standalone questions.

### Final Result

**92% overall**

On the final evaluation subsets:

| Category | Result |
|---|---:|
| Follow-up detection | **100%** |
| Standalone detection | **100%** |
| Ambiguous cases | **100%** |

For detected follow-up questions, the most recent previous user message is combined with the current question to improve retrieval context.

The evaluation focused on whether the detector correctly distinguished context-dependent questions from questions that could be handled independently.

---

## 7. Selective Conversational History

Selective history was compared against two baselines:

1. Current question only
2. Always include history

### Retrieval Results

| Retrieval strategy | Top-1 | Top-3 |
|---|---:|---:|
| Current question only | 43.8% | 62.5% |
| Always include history | 62.5% | 75.0% |
| **Selective history** | **75.0%** | **100%** |

Compared with the current-question-only baseline, selective history improved:

- **Top-1 by +31.2 percentage points**
- **Top-3 by +37.5 percentage points**

The evaluation also showed that indiscriminately including older conversation history could introduce regression.

The selective approach was therefore retained to incorporate useful conversational context without blindly passing all historical turns.

---

## 8. Production End-to-End Evaluation

The final deployed system was tested end-to-end using the production application and API.

### Result

**11/12 clean PASS + 1 known limitation**

The production evaluation covered:

- Normal well-being questions
- Stress and relaxation
- Sleep-related queries
- Unsupported treatment requests
- Unsupported numerical/general knowledge requests
- Crisis scenarios
- Medication-related restricted scenarios
- Restrictive/eating-related scenarios
- Topic switching
- Harmless conversation history
- Context-dependent follow-up behavior

### Known Production Limitation

A context-dependent interaction such as:

```text
User: How can I manage daily stress?
User: What should I try first?
```