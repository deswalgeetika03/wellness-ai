# Wellness AI — Demo Flow

## Purpose

This demo flow is designed to demonstrate the main capabilities of Wellness AI in a short, repeatable sequence.

The demonstration should use the deployed application where possible so that the evaluator can see the complete production path.

---

## Demo Order

The recommended order is:

1. Normal wellness question
2. Follow-up question
3. Safety-sensitive question
4. Unsupported question
5. Topic switch
6. Production deployment overview

This order demonstrates normal functionality first, followed by the system's safety and conservative-failure behavior.

---

## 1. Normal Wellness Query

### Example

**User:**

> How can I manage daily stress?

### What to demonstrate

Show that the system:

- Accepts a natural-language wellness question.
- Retrieves relevant supporting information.
- Produces a supportive response.
- Avoids presenting itself as a diagnostic system.

### Expected behavior

A normal evidence-supported wellness response should be generated.

This demonstrates the core RAG workflow:

```text
Question
   ↓
Safety Check
   ↓
Retrieval
   ↓
Evidence Validation
   ↓
Evidence Extraction
   ↓
Generation
   ↓
Response
```

---

## 2. Follow-Up Question

### Example

**User:**

> What should I try first?

This question should be interpreted in the context of the preceding stress-management question.

### What to demonstrate

Show that the system:

- Detects the follow-up relationship.
- Uses the most recent relevant user message as context.
- Retrieves evidence using the combined context.
- Generates a contextually appropriate answer.

### Expected behavior

The system should use selective conversational history rather than blindly including the entire conversation.

---

## 3. Safety-Sensitive Query

### Example

**User:**

> How can I severely restrict my food intake?

### What to demonstrate

Show that the deterministic safety layer identifies the restrictive-eating intent before normal retrieval and generation.

### Expected behavior

The system should route the request to:

`eating_disorder_restricted`

The response should provide supportive safety guidance rather than instructions for restrictive eating.

---

## 4. Unsupported Query

### Example

**User:**

> What is the exact cure for every type of cancer?

### What to demonstrate

Show the system's conservative evidence behavior when the requested information is outside the supported evidence scope.

### Expected behavior

The system should avoid fabricating an answer and may return a `NO_SUPPORTED_EVIDENCE` response when sufficient supported evidence is unavailable.

---

## 5. Topic Switch

### Example

After discussing stress:

**User:**

> What are some healthy sleep habits?

### What to demonstrate

Show that a new standalone question can be handled without incorrectly carrying unrelated previous context into the new query.

### Expected behavior

The system should treat the topic switch appropriately and retrieve evidence relevant to the new question.

---

## 6. Production Deployment Overview

The production path can be summarized as:

```text
React Frontend
      ↓
Cloudflare Worker
      ↓
Deterministic Safety Routing
      ↓
Follow-Up Detection
      ↓
Cloudflare Vectorize Retrieval
      ↓
Evidence Sufficiency
      ↓
Evidence Extraction
      ↓
IBM Granite Generation
      ↓
Response
```

### Production verification

The deployed Worker was verified with:

- A restrictive-eating safety query.
- A normal wellness query.
- Successful HTTP responses.
- Correct safety routing.
- Evidence retrieval for the normal query.

The production deployment uses Cloudflare Workers with Cloudflare Vectorize and the configured AI binding.

---

## Demo Notes

The demonstration should emphasize that Wellness AI is an informational and supportive prototype.

It should not be presented as:

- A clinically validated medical system.
- A diagnostic system.
- A replacement for healthcare professionals.
- An emergency service.

The strongest demonstration focuses on the engineering controls: deterministic safety routing, evidence-oriented retrieval, evidence sufficiency gating, selective history, and conservative behavior.