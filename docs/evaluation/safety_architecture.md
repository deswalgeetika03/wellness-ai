# Wellness AI — Safety Architecture

## Overview

Wellness AI treats safety as a deterministic routing concern rather than relying entirely on generative model behavior.

The safety layer is evaluated before normal retrieval and generation for applicable sensitive scenarios. This allows predefined safety-sensitive categories to be handled through controlled response paths instead of being passed through the normal RAG generation pipeline.

The design is intended to reduce the risk of inappropriate generated responses in sensitive situations.

---

## 1. High-Level Safety Flow

The production query flow begins with deterministic safety routing:

```text
User Question
      |
      v
Deterministic Safety Layer
      |
      +----------------------+
      |                      |
   Sensitive                Normal
      |                      |
      v                      v
Safety Response       Follow-up / Context
      |                      |
      v                      v
     STOP                 Retrieval
                             |
                             v
                       Evidence Checks
                             |
                             v
                         Generation
                             |
                             v
                          Response
```

---

## 2. Safety Priority

Safety routing occurs before normal retrieval and generation.

The current user question is prioritized when determining the safety route so that unrelated conversation history does not override the current safety intent.

---

## 3. Safety Categories

The deterministic safety layer includes routing for sensitive categories such as:

- Crisis-related requests.
- Medication-related restricted requests.
- Restrictive/eating-related requests.
- Other predefined safety-sensitive scenarios.

Normal wellness questions continue through the standard RAG pipeline.

---

## 4. Restrictive-Eating Coverage

During the Phase 7 release audit, an additional restrictive-eating paraphrase gap was identified outside the original frozen Phase 5 benchmark.

The implementation was expanded to detect restrictive-intent patterns such as requests to severely restrict food intake or eat as little as possible.

Additional regression coverage achieved:

- Local restrictive/eating detection: **8/8 PASS**
- Production safety tests: **17/17 PASS**
- Full Cloudflare Worker tests: **26/26 PASS**

The original frozen Phase 5 benchmark remains **12/12 PASS**.

---

## 5. Design Principle

The safety architecture is intended to provide deterministic handling for predefined sensitive scenarios before the generative model is invoked.

This reduces reliance on generation-time safety behavior and makes the safety routing logic directly testable.