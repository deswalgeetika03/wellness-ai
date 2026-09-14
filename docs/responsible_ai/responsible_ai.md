# Wellness AI — Responsible AI

## Overview

Responsible AI is treated as a core engineering consideration in Wellness AI rather than as a separate presentation layer.

The system combines deterministic safety routing, evidence-oriented retrieval, conservative evidence gating, transparent evaluation, and explicit limitations to reduce foreseeable risks associated with a generative wellness assistant.

Wellness AI is designed as an informational and supportive prototype. It is not intended to diagnose conditions, replace qualified professionals, or provide emergency services.

---

## 1. Safety

Safety-sensitive scenarios are handled through a deterministic routing layer before normal retrieval and generation.

The safety flow is:

```text
User Question
      |
      v
Deterministic Safety Layer
      |
      +---- Sensitive ---> Controlled Safety Response
      |
      +---- Normal ------> Normal RAG Pipeline
```

This approach makes safety routing explicit and testable rather than depending entirely on the generative model.

---

## 2. Grounding

The system uses retrieval and evidence sufficiency checks to reduce unsupported responses.

When sufficient evidence is unavailable, the system can return a conservative `NO_SUPPORTED_EVIDENCE` response rather than generating from unsupported model knowledge.

---

## 3. Transparency

The project documents:

- Evaluation methodology.
- Final evaluation results.
- Known limitations.
- Design decisions.
- Safety architecture.
- Production deployment behavior.

Known failures are retained in the evaluation record rather than being hidden.

---

## 4. Conservative Behavior

The system is designed to fail conservatively when supported evidence is insufficient.

This is particularly important for a wellness-oriented assistant because unsupported or overly confident responses can create misleading impressions of reliability.

---

## 5. Human Oversight

Wellness AI is positioned as an informational and supportive prototype.

It is not an autonomous medical decision-maker and should not be used as a replacement for qualified healthcare professionals or emergency services.

---

## 6. Evaluation-Based Claims

The project uses measured evaluation results rather than broad claims of accuracy or safety.

Examples include:

- **67.5%** Top-1 retrieval.
- **97.5%** Top-3 retrieval.
- **90%** generation success.
- **93.75%** applicable grounding.
- **12/12** established deterministic safety-suite PASS.
- **75% / 100%** selective-history Top-1 / Top-3.

These results describe the defined internal evaluations and should not be interpreted as clinical validation.

---

## 7. Limitations

The system has known limitations, including:

- Retrieval Top-1 performance below perfect accuracy.
- A known follow-up evidence-gate limitation in production.
- Two unsupported-claim failures in the final generation evaluation.
- Non-exhaustive paraphrase and adversarial safety coverage.

These limitations are part of the project's evaluation record.

---

## 8. Responsible-AI Principle

The central responsible-AI principle is to combine technical controls with transparent evaluation.

The project does not claim that deterministic routing, retrieval, evidence gating, or generation controls eliminate all risks. Instead, these mechanisms are used to make important system behavior more controlled, testable, and transparent.