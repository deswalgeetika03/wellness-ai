# Wellness AI â€” Known Limitations

## Overview

Wellness AI is an evaluated prototype rather than a clinically validated system.

The evaluation process intentionally preserves known failures, coverage gaps, and trade-offs instead of presenting only successful results.

This document consolidates the principal limitations identified during development and evaluation.

---

## 1. Retrieval Top-1 Performance

The final retrieval configuration achieved:

- **67.5% Top-1**
- **97.5% Top-3**

The difference indicates that the correct evidence is frequently present within the retrieved context but is not always ranked as the single highest-scoring result.

The source-diversity constraint improved Top-3 retrieval from **90.0% to 97.5%** without changing Top-1 performance.

### Impact

A downstream stage may receive the correct supporting material even when the first-ranked result is not the ideal individual source.

### Future direction

Further retrieval ranking and knowledge-base improvements could target Top-1 performance without unnecessarily increasing context size.

**Owning area:** Retrieval / future evaluation.

---

## 2. Follow-Up Verification

The previously documented production limitation involved a context-dependent follow-up question. The exact scenario was subsequently re-tested against the deployed production system.

The exact tested interaction was:

```text
User: How can I manage daily stress?

User: What should I try first?
```


The deployed API and frontend successfully used the preceding user message as conversational context and returned a grounded response with verified evidence and sources.

The limitation is therefore considered **resolved for this tested scenario**.

This does not establish exhaustive coverage of all possible conversational follow-up patterns. Broader adversarial and paraphrase testing remains future evaluation work.
