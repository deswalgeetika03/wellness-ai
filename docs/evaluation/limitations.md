# Wellness AI — Known Limitations

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

## 2. Follow-Up Evidence-Gate Limitation

A known production limitation occurs with some context-dependent follow-up questions.

For example:

```text
User: How can I manage daily stress?

User: What should I try first?
```