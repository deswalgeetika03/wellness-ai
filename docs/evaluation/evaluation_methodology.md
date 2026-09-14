# Evaluation Methodology

Wellness AI was evaluated through separate, targeted benchmarks rather than relying on a single overall chatbot score.

The evaluation process covers:

1. Retrieval quality
2. Safety routing
3. Generation and grounding
4. Conversational history and follow-up behavior
5. Production end-to-end behavior

Each evaluation was designed around a specific system component so that failures could be traced back to the relevant stage of the pipeline.

---

## 1. Retrieval Evaluation

### Dataset

The retrieval benchmark contains **40 questions**:

* **20 textbook-style questions**
* **20 casual/user-style questions**

The two categories were evaluated separately because conversational phrasing can behave differently from more explicit textbook-style queries.

### Metrics

Two retrieval metrics were used:

* **Top-1:** whether the correct source appears as the highest-ranked result.
* **Top-3:** whether the correct source appears within the final top-three retrieved results.

### Final Configuration

The evaluated retrieval configuration used:

* `sentence-transformers/all-MiniLM-L6-v2`
* Candidate pool: **10**
* Final context: **3**
* Maximum chunks per source: **1**
* Cosine similarity

The source-diversity constraint was evaluated experimentally and improved Top-3 retrieval from **90.0% to 97.5%** without changing Top-1 performance.

### Final Result

| Metric |    Result |
| ------ | --------: |
| Top-1  | **67.5%** |
| Top-3  | **97.5%** |

The retrieval evaluation therefore measures both ranking quality and whether useful evidence is available within the final context.

---

## 2. Safety Evaluation

Safety was evaluated separately from normal generation because sensitive queries are intentionally routed before normal retrieval and generation.

### Deterministic Safety Suite

The local safety evaluation contains **12 test cases** covering scenarios including:

* Crisis
* Medication-related requests
* Restrictive/eating-related requests
* Normal wellness questions
* Safety-priority conflicts

### Metric

The primary criterion is whether the system selects the intended safety route.

### Final Result

**12/12 tests passed.**

Production validation additionally tested representative sensitive and normal scenarios, including crisis, medication restriction, restrictive eating, normal wellness questions, unsupported requests, and topic switching.

The established 12-case suite remains the frozen Phase 5 benchmark and is not retroactively changed. During the Phase 7 release audit, an additional restrictive-eating paraphrase gap was identified outside that benchmark. The safety implementation was updated to cover the missed restrictive-intent patterns, followed by regression validation of the expanded cases. The original benchmark result therefore remains **12/12**, while the additional regression coverage is recorded separately.

---

## 3. Generation and Grounding Evaluation

Generation was evaluated using a manually reviewed **20-question evaluation set**.

The evaluation considers:

* Whether the generated answer is acceptable
* Whether the response is appropriately grounded
* Whether unsupported claims are introduced
* Whether the tone is appropriate
* Whether diagnostic labels are incorrectly presented

### Generation Metric

The final frozen generation evaluation achieved:

**18/20 successful evaluations — 90%.**

This improved from the historical generation baseline of:

**16/20 — 80%.**

### Grounding Metric

Grounding is reported only over applicable cases.

The final result was:

**15/16 applicable cases grounded — 93.75%.**

The complete 20-question set contained:

* 15 grounded cases
* 2 unsupported-claim failures
* 3 safety/N/A cases

The two unsupported-claim failures remain documented as limitations rather than being removed from the evaluation record.

### Additional Response Checks

* Appropriate tone: **20/20**
* Diagnostic-label avoidance: **20/20**

---

## 4. Conversational Evaluation

Conversation behavior was evaluated separately because a context-aware assistant must be tested on both follow-up questions and standalone questions.

### Selective History Benchmark

The evaluation compared three strategies:

1. Current question only
2. Always include history
3. Selective history

### Results

| Strategy               |     Top-1 |    Top-3 |
| ---------------------- | --------: | -------: |
| Current question only  |     43.8% |    62.5% |
| Always include history |     62.5% |    75.0% |
| **Selective history**  | **75.0%** | **100%** |

Selective history improved over the current-question-only baseline by:

* **+31.2 percentage points Top-1**
* **+37.5 percentage points Top-3**

The evaluation also showed that indiscriminately including older history could cause regression, which supported the selective-history design.

---

## 5. Follow-Up Detection Evaluation

The follow-up detector was evaluated independently from retrieval quality.

The final evaluation measured:

* Overall detection
* Follow-up cases
* Standalone cases
* Ambiguous cases

### Final Result

**92% overall**

with:

* **100% follow-up**
* **100% standalone**
* **100% ambiguous**

on the final evaluated subsets.

This separates the question of:

> “Did the system recognize that this is a follow-up?”

from:

> “Did retrieval find the right evidence?”

That distinction makes failures easier to diagnose.

---

## 6. Safety Across Conversation History

Safety was also tested in the presence of conversation context.

The current user question remains the authoritative input for safety routing.

This prevents unrelated previous conversation context from overriding the current safety classification.

Validated scenarios included:

* Crisis
* Medication
* Restrictive eating

---

## 7. Production End-to-End Evaluation

The deployed production system was evaluated separately from the local component benchmarks.

The final production evaluation used **12 representative cases** covering:

* Normal wellness questions
* Sleep/relaxation
* Unsupported treatment requests
* Unsupported numerical/general-knowledge questions
* Crisis
* Medication
* Restrictive eating
* Topic switching
* Harmless conversation history
* Context-dependent follow-up behavior

### Final Result

**11/12 clean PASS + 1 known limitation**

The known limitation involved a context-dependent follow-up that could return:

```text
NO_SUPPORTED_EVIDENCE
```

even when the conversation context was useful.

The evidence gate was deliberately not weakened simply to make this test pass.

---

## 8. Evaluation Principles

The evaluation process follows several principles.

### Component-specific evaluation

Each major subsystem is evaluated independently before relying on end-to-end behavior.

### Reproducibility

Frozen benchmark results are preserved rather than rewritten after later changes.

### Failure visibility

Known failures remain documented instead of being removed from evaluation sets.

### Regression protection

Changes are accepted only when they demonstrate sufficient improvement without introducing unacceptable regressions.

### Separation of historical and current results

A later fix does not rewrite an earlier frozen benchmark.

If a post-freeze change modifies behavior, its new result is treated as a separate post-fix evaluation.

---

## 9. Interpretation

The evaluation results should be interpreted as **prototype engineering measurements**, not clinical validation.

The benchmarks demonstrate how the system behaves on the selected test sets and production scenarios.

They do not establish:

* Clinical effectiveness
* Medical accuracy certification
* Diagnostic capability
* Real-world health outcomes
* Generalization to all possible user queries

The purpose of the evaluation is to measure system behavior, identify failure modes, and support evidence-based engineering decisions.
