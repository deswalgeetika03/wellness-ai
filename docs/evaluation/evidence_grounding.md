# Wellness AI — Evidence & Grounding

## Overview

Evidence grounding is a central design principle of Wellness AI.

The system is designed to avoid generating unsupported responses when sufficient evidence is not available. To achieve this, retrieval, evidence validation, evidence extraction, and generation are treated as separate responsibilities.

The evidence-oriented pipeline is designed to provide the generation model with a supported basis for its response rather than relying only on the model's internal knowledge.

---

## 1. Evidence-Oriented Pipeline

The normal query flow can be represented as:

```text
User Question
      |
      v
Safety Routing
      |
      v
Retrieval
      |
      v
Evidence Sufficiency Check
      |
      +---- Insufficient
      |        |
      |        v
      |  NO_SUPPORTED_EVIDENCE
      |
      +---- Sufficient
               |
               v
        Evidence Extraction
               |
               v
        Supported Evidence
               |
               v
        Granite Generation
               |
               v
            Response
```

---

## 2. Evidence Sufficiency

The system applies an evidence sufficiency gate before generation.

If retrieved evidence does not meet the required similarity threshold, the system does not proceed to normal generation.

Instead, it returns a conservative `NO_SUPPORTED_EVIDENCE` response.

This prevents the generation model from being used as an unrestricted fallback when the retrieval stage does not provide sufficient supported evidence.

---

## 3. Evidence Extraction

When sufficient evidence is available, the selected retrieval results are processed into supported evidence for the generation stage.

The goal is to provide the model with a constrained evidence basis rather than simply passing arbitrary retrieved text.

---

## 4. Grounding Evaluation

Grounding was evaluated separately from overall generation success.

The final applicable grounding result was:

**15/16 grounded — 93.75%**

Three cases in the full 20-case generation evaluation were safety or otherwise non-applicable to grounding.

The project therefore reports **93.75% applicable grounding**, rather than treating 15/20 as the grounding accuracy.

---

## 5. Known Limitation

Two generation evaluations contained unsupported claims.

These cases remain part of the final evaluation record and are documented as known limitations.

The evidence-oriented architecture reduces unsupported generation risk but does not establish perfect factual accuracy or exhaustive grounding.

---

## 6. Design Principle

The project treats retrieval, evidence sufficiency, evidence extraction, and generation as separate stages.

This separation makes it possible to:

- Evaluate retrieval independently.
- Reject insufficient evidence.
- Provide supported evidence to generation.
- Preserve known failures in the evaluation record.
- Avoid presenting the system as clinically validated.