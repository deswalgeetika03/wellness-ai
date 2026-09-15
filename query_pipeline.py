"""
query_pipeline.py

End-to-end Wellness RAG pipeline:

    User question
        |
        v
    Deterministic safety layer
        |
        +-- crisis / ED-numeric --> safe response, STOP
        |
        v
    ChromaDB retrieval
        |
        v
    Source-diversity selection
        |
        v
    Grounded prompt
        |
        v
    Granite via Ollama
        |
        v
    Answer + sources

The retrieval stage uses the source-diversity strategy tested in
evaluate_retrieval.py. It fetches a wider candidate pool and prefers
different source documents so that a large source cannot dominate
the final context simply because it has more chunks.
"""

import argparse
import os
import sys
import re
import time
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace",
        )
        sys.stderr.reconfigure(
            encoding="utf-8",
            errors="replace",
        )
    except AttributeError:
        pass

import requests
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from safety_layer import route_query



# ============================================================
# MEDICATION REQUEST CHECK
# ============================================================

MEDICATION_PATTERNS = [
    r"\bwhat medication\b",
    r"\bwhat medicine\b",
    r"\bwhich medication\b",
    r"\bwhich medicine\b",
    r"\bwhat drug\b",
    r"\bwhich drug\b",
    r"\bwhat should i take\b",
    r"\bwhat can i take\b",
    r"\bmedicine for\b",
    r"\bmedication for\b",
    r"\bdrug for\b",
]

_MEDICATION_REGEX = re.compile(
    "|".join(MEDICATION_PATTERNS),
    re.IGNORECASE
)

MEDICATION_RESPONSE = (
    "I can't recommend or select a specific medication for anxiety. "
    "A qualified healthcare professional can assess your situation and "
    "discuss appropriate treatment options, including potential benefits "
    "and side effects. If your symptoms are severe, worsening, or "
    "interfering with daily life, consider seeking professional support."
)


def check_medication_request(user_input: str) -> bool:
    return bool(_MEDICATION_REGEX.search(user_input))



# ============================================================
# CONFIG
# ============================================================

TOP_K = 3
CANDIDATE_K = 10
MAX_PER_SOURCE = 1
EVIDENCE_DISTANCE_THRESHOLD = 1.25

# Targeted candidate-generation fallback for strong panic/death wording.
# This does not change the normal retrieval strategy.
PANIC_FALLBACK_QUERY = "panic attack fear of death impending doom"

PANIC_FALLBACK_PATTERNS = [
    r"\bfelt like i was dying\b",
    r"\bfeel like i'm dying\b",
    r"\bfeel like i am dying\b",
    r"\bfeeling like i'm dying\b",
    r"\bfeeling like i am dying\b",
    r"\bfear of death\b",
    r"\bimpending doom\b",
]

OLLAMA_URL = os.getenv(
    "WELLNESS_OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

# IMPORTANT:
# Change this if `ollama list` shows a different Granite model tag.
GRANITE_MODEL = "granite4.1:3b"

TEMPERATURE = 0.3
_embeddings = None


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT_TEMPLATE = """Role: You are a supportive wellness information assistant.

Task: Answer the user's current question using the verified evidence
and conversation context provided below.

The Verified evidence section contains the only factual Wellness
information that may be used in the answer.

Conversation context is important for understanding what the user
means when they use words such as "it", "this", "that", "they", "them",
"more", or other short follow-up questions.

Use earlier conversation to resolve references and understand the
user's situation. Do not treat the current question as an isolated
question when the conversation provides relevant context.

Reference resolution rules:
- For vague follow-up words such as "this", "that", "it", "these",
  "those", "more", or "what about it", use the Most recent User
  message as the primary reference.
- The Most recent User message is the default subject when the
  current question does not explicitly name a topic.
- Answer the current question primarily about that subject.
- Do not switch to an older topic merely because the older topic
  is more prominent in the conversation.
- Older conversation may provide supporting context, but it must
  not replace the primary subject identified by the Most recent
  User message.
- If the user asks "What should I do about this?" immediately after
  discussing a topic, interpret "this" as that immediately preceding
  topic.

The conversation context contains previous User and Assistant
messages.

Previous User messages describe what the user actually said.
Previous Assistant messages are prior responses generated by the
assistant and must not be treated as facts about the user's life,
symptoms, history, preferences, or circumstances unless the user
explicitly confirmed those details.

Use previous User messages to understand the user's situation,
preferences, and intent.

Use the Wellness knowledge for factual wellness information.
Previous Assistant messages may help preserve conversational
continuity, but they are not an independent source of truth.

Do not introduce facts, treatments, numbers, or recommendations that
are not supported by the Wellness knowledge.

Verified evidence:
{verified_evidence}

Verified evidence is the ONLY Wellness knowledge available for
factual answering.

Do not use, reconstruct, or infer additional facts from retrieval
results that are not included in Verified evidence.

Evidence-first answering:
- Before writing the answer, identify the specific information in
  Verified evidence that directly supports the answer.

- Verified evidence is the ONLY source of factual Wellness information
  that may be used in the answer.

- No broader retrieval context is available for factual answering.
  Use only Verified evidence.

- Do not infer, elaborate, generalize, or complete missing information
  using pretrained knowledge.

- If a detail is not explicitly present in Verified evidence, leave it
  out.

- If Verified evidence supports only part of the question, answer only
  that supported part and clearly avoid unsupported portions.

- Never add symptoms, causes, treatments, recommendations, examples,
  durations, diagnostic criteria, or explanations unless they are
  explicitly included in Verified evidence.

- Never apply a named disorder or condition from Verified evidence to
  the user's personal symptoms.

- If Verified evidence describes a disorder or condition, present that
  information only as general educational information.

- Do not say the user's symptoms are "related to", "consistent with",
  "suggestive of", or "possibly" that disorder unless the provided
  evidence explicitly establishes that relationship for the individual
  user.

- If the user describes personal symptoms and the evidence only gives
  general information about a disorder or condition, present that
  information as general educational information rather than applying
  the label to the user.

- For questions asking for types, causes, symptoms, treatments,
  techniques, or recommendations, include only the items explicitly
  supported by Verified evidence.

- Prefer a shorter evidence-supported answer over a more complete
  answer containing unsupported information.

- Do not mention this evidence-checking process in the final answer.

Format:
Answer directly and concisely.
For simple questions, use 2–4 sentences.
Use a short numbered or bulleted list only when needed.
Do not repeat information.
Do not add unnecessary background information or closing remarks.
Use clear, supportive language.
No unnecessary medical jargon.

Exclusions:
- Never diagnose, prescribe, recommend, select, or compare
  specific medications or dosages. If medication is relevant, state only
  that a qualified healthcare professional can discuss treatment options.

- Never diagnose or label the user's personal symptoms with a named
  mental-health disorder.

- When a user describes personal symptoms and asks what they were,
  do not identify the symptoms as a specific disorder or state that
  the user had, has, may have, might have, or may be experiencing
  that disorder.

- If the retrieved Wellness knowledge describes those symptoms in
  relation to a disorder, explain the general educational connection
  without applying the disorder label to the user's individual
  experience.

- Prefer wording such as "Those symptoms can occur during panic
  attacks" rather than "That sounds like a panic attack."

- If the available context is insufficient to determine what caused
  the user's symptoms, say that the symptoms can have different
  causes and that the available information cannot determine the cause.

- Keep every factual claim grounded in Verified evidence.

- Use only symptoms, causes, treatments, coping strategies, definitions,
  numbers, timeframes, or other factual details that are explicitly
  supported by Verified evidence.

- Do not expand a retrieved definition with additional symptoms,
  diagnostic criteria, causes, treatments, examples, or clinical details
  from general knowledge.

- Do not add specific techniques, methods, routines, or recommendations
  unless they are explicitly supported by Verified evidence.

- When Verified evidence supports only part of the answer, answer only
  that supported part. Do not fill the missing part from general
  knowledge.

- If Verified evidence does not contain enough information to answer the
  question, say so honestly instead of completing the answer from
  pretrained knowledge.

- Treat previous Assistant messages as conversational context only.
  They are not evidence for factual Wellness claims.

- Do not claim that the user previously said, experienced, preferred,
  or did something unless that information appears in a previous User
  message.

- Avoid broad normalizing or reassuring statements about the user's
  personal symptoms, such as "this is completely normal" or "this is
  common," unless the provided Context directly supports that framing.

- Never invent facts that are not present in the Context.

{history_block}
Use the conversation context to understand the user's intent and
resolve references in the current question.

Question:
{question}
"""


# ============================================================
# LOAD VECTOR DATABASE
# ============================================================

def get_vector_db():
    global _embeddings

    if _embeddings is None:
        embedding_start = time.perf_counter()

        _embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={
        "local_files_only": True
    },
    show_progress=False
)

        embedding_time = time.perf_counter() - embedding_start

        print(
            f"[PERFORMANCE] Embedding model initialization: "
            f"{embedding_time:.3f}s"
        )

    chroma_start = time.perf_counter()

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    chroma_time = time.perf_counter() - chroma_start

    print(
        f"[PERFORMANCE] Chroma initialization: "
        f"{chroma_time:.3f}s"
    )

    return vector_db

# ============================================================
# SOURCE-DIVERSITY RETRIEVAL
# ============================================================

def retrieve_context(
    vector_db,
    question: str,
    k: int = TOP_K,
    candidate_k: int = CANDIDATE_K,
    max_per_source: int = MAX_PER_SOURCE,
):
    """
    Retrieve a wider candidate pool, then select up to k chunks while
    limiting the number of chunks from the same source.

    The original source-diversity selection strategy is preserved.
    Retrieval distances are retained so Phase 6 can assess whether
    sufficient evidence exists before generation.
    """

        # --------------------------------------------------------
    # NORMAL CANDIDATE GENERATION
    # --------------------------------------------------------
    # Preserve the original Top-10 similarity retrieval.
    candidates = vector_db.similarity_search_with_score(
        question,
        k=candidate_k,
    )

    candidate_docs = [
        (doc, float(score))
        for doc, score in candidates
    ]

    # --------------------------------------------------------
    # TARGETED PANIC CANDIDATE FALLBACK
    # --------------------------------------------------------
    # For strong panic/death wording, run a second semantic
    # retrieval using a concept query that is known to retrieve
    # the relevant panic evidence reliably.
    #
    # IMPORTANT:
    # - Normal retrieval remains unchanged.
    # - Source-diversity selection below remains unchanged.
    # - No source_id is hard-coded.
    # --------------------------------------------------------

    question_lower = question.lower()

    panic_fallback_triggered = any(
        re.search(
            pattern,
            question_lower,
        )
        for pattern in PANIC_FALLBACK_PATTERNS
    )

    if panic_fallback_triggered:

        print(
            "[RETRIEVAL FALLBACK] "
            "Strong panic/death wording detected. "
            f"Running targeted query: {PANIC_FALLBACK_QUERY}"
        )

        fallback_candidates = (
            vector_db.similarity_search_with_score(
                PANIC_FALLBACK_QUERY,
                k=candidate_k,
            )
        )

        # Add fallback candidates after the original candidates.
        # The existing source-diversity selection will decide
        # which chunks ultimately enter the final context.
        existing_ids = {
            id(doc)
            for doc, _ in candidate_docs
        }

        for doc, score in fallback_candidates:

            if id(doc) in existing_ids:
                continue

            candidate_docs.append(
                (doc, float(score))
            )

            existing_ids.add(id(doc))

        # Re-sort the merged candidate pool by retrieval distance.
        # Lower distance means stronger semantic similarity.
        candidate_docs.sort(
            key=lambda item: item[1]
        )

    selected = []
    source_counts = {}

    # First pass:
    # Prefer one chunk from each source.
    for doc, score in candidate_docs:

        source_id = str(
            doc.metadata.get("source_id", "?")
        )

        count = source_counts.get(
            source_id,
            0,
        )

        if count >= max_per_source:
            continue

        selected.append(
            (doc, score)
        )

        source_counts[source_id] = count + 1

        if len(selected) >= k:
            break

    # Fallback:
    # If there aren't enough distinct sources, fill remaining slots
    # using the original similarity ranking.
    if len(selected) < k:

        selected_ids = {
            id(doc)
            for doc, _ in selected
        }

        for doc, score in candidate_docs:

            if id(doc) in selected_ids:
                continue

            selected.append(
                (doc, score)
            )

            if len(selected) >= k:
                break

    context = [
        {
            "text": doc.page_content,
            "source_id": str(
                doc.metadata.get(
                    "source_id",
                    "?",
                )
            ),
            "title": doc.metadata.get(
                "title",
                "Unknown source",
            ),
            "organization": doc.metadata.get(
                "organization",
                "Unknown",
            ),
             "retrieval_distance": score,
        }
        for doc, score in selected
    ]

    best_distance = candidate_docs[0][1]

    return context, best_distance

# ============================================================
# CONVERSATION CONTEXT
# ============================================================

RECENT_MESSAGES = 6
MAX_RELEVANT_OLDER_UNITS = 5
RELEVANCE_THRESHOLD = 0.30


def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two embedding vectors.
    """

    a = np.asarray(a)
    b = np.asarray(b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def build_conversation_units(history: list) -> list:
    """
    Group conversation turns into user/assistant units.

    Each user message is paired with the assistant response
    immediately following it, when available.

    This preserves the meaning of a conversation exchange
    instead of evaluating individual messages in isolation.
    """

    units = []

    index = 0

    while index < len(history):

        message = history[index]

        if message.get("role") != "user":
            index += 1
            continue

        user_content = str(
            message.get("content", "")
        ).strip()

        if not user_content:
            index += 1
            continue

        unit_messages = [message]

        # Pair the user's message with the following
        # assistant response when one exists.
        if (
            index + 1 < len(history)
            and history[index + 1].get("role") == "assistant"
        ):
            unit_messages.append(history[index + 1])

            index += 2

        else:
            index += 1

        units.append(
            {
                "messages": unit_messages,
                "start_index": index - len(unit_messages),
            }
        )

    return units


def format_conversation_unit(unit: dict) -> str:
    """
    Convert a conversation unit into text suitable for embedding.
    """

    lines = []

    for message in unit["messages"]:

        role = message.get("role")

        speaker = (
            "User"
            if role == "user"
            else "Assistant"
        )

        content = str(
            message.get("content", "")
        ).strip()

        if content:
            lines.append(
                f"{speaker}: {content}"
            )

    return "\n".join(lines)


def select_conversation_context(
    question: str,
    history: list | None = None,
) -> list:
    """
    Select conversation context.

    For vague follow-up questions such as "this", "that", "it",
    or "more", the immediately preceding User message is treated
    as the primary reference.

    For normal questions, recent conversation plus semantically
    relevant older conversation is retained.
    """

    if not history:
        return []

    # --------------------------------------------------------
    # Detect vague follow-up question
    # --------------------------------------------------------

    vague_patterns = [
        r"\bwhat should i try first\b",
        r"\bwhat should i try\b",
        r"\bwhat do i try first\b",
        r"\bwhat should i do about this\b",
        r"\bwhat should i do about that\b",
        r"\bwhat can i do about this\b",
        r"\bwhat can i do about that\b",
        r"\bwhat about this\b",
        r"\bwhat about that\b",
        r"\bwhat about it\b",
        r"\bhow do i handle this\b",
        r"\bhow do i handle that\b",
        r"\bcan you give me more\b",
        r"\bgive me more\b",
    ]

    is_vague_reference = any(
        re.search(
            pattern,
            question.strip().lower(),
        )
        for pattern in vague_patterns
    )

    # --------------------------------------------------------
    # Deterministic handling for vague references
    # --------------------------------------------------------

    if is_vague_reference:

        # Find the most recent User message before the current
        # question.
        previous_user_messages = [
            message
            for message in history
            if message.get("role") == "user"
        ]

        if not previous_user_messages:
            return history[-RECENT_MESSAGES:]

        latest_user_message = previous_user_messages[-1]

        latest_user_index = history.index(
            latest_user_message
        )

        # Include the previous exchange plus a small amount
        # of recent context for conversational continuity.
        start_index = max(
            0,
            latest_user_index - 1,
        )

        return history[start_index:]

    # --------------------------------------------------------
    # Normal conversation handling
    # --------------------------------------------------------

    if len(history) <= RECENT_MESSAGES:
        return history

    recent = history[-RECENT_MESSAGES:]
    older = history[:-RECENT_MESSAGES]

    # --------------------------------------------------------
    # Build conversation units from older history.
    # --------------------------------------------------------

    units = build_conversation_units(older)

    if not units:
        return recent

    # --------------------------------------------------------
    # Create embeddings using the same model as the RAG system.
    # --------------------------------------------------------

    embeddings = _embeddings

    question_embedding = embeddings.embed_query(
        question
    )

    scored_units = []

    for unit in units:

        # Use only the user's message for semantic relevance.
        user_message = unit["messages"][0]

        unit_text = str(
            user_message.get("content", "")
        ).strip()

        if not unit_text:
            continue

        unit_embedding = embeddings.embed_query(
            unit_text
        )

        semantic_score = cosine_similarity(
            question_embedding,
            unit_embedding,
        )

        if len(units) > 1:
            recency_score = (
                unit["start_index"] / (len(older) - 1)
            )
        else:
            recency_score = 1.0

        combined_score = (
            semantic_score * 0.70
            + recency_score * 0.30
        )

        scored_units.append(
            {
                "unit": unit,
                "score": combined_score,
                "semantic_score": semantic_score,
            }
        )

    # --------------------------------------------------------
    # Rank older conversation units.
    # --------------------------------------------------------

    scored_units.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    relevant_units = [
        item
        for item in scored_units[
            :MAX_RELEVANT_OLDER_UNITS
        ]
        if item["semantic_score"] >= RELEVANCE_THRESHOLD
    ]

    # --------------------------------------------------------
    # Restore chronological order.
    # --------------------------------------------------------

    relevant_units.sort(
        key=lambda item: item["unit"]["start_index"]
    )

    # --------------------------------------------------------
    # Flatten selected units.
    # --------------------------------------------------------

    older_messages = []

    for item in relevant_units:
        older_messages.extend(
            item["unit"]["messages"]
        )

    # --------------------------------------------------------
    # Return older relevant context followed by recent context.
    # --------------------------------------------------------

    return older_messages + recent

# ============================================================
# PROMPT CONSTRUCTION
# ============================================================

def build_prompt(
    question: str,
    chunks: list,
    history: list | None = None,
) -> tuple[str, str]:

    conversation_context = select_conversation_context(
        question,
        history,
    )

    context_block = "\n\n".join(
        f"[{chunk['organization']} - {chunk['title']}]\n"
        f"{chunk['text']}"
        for chunk in chunks
    )

    verified_evidence = extract_supported_evidence(
        question,
        chunks,
    )

    
    if conversation_context:
        lines = ["Conversation context:"]

        for turn in conversation_context:
            speaker = (
                "User"
                if turn["role"] == "user"
                else "Assistant"
            )

            lines.append(
                f"{speaker}: {turn['content']}"
            )

        history_block = "\n".join(lines) + "\n\n"

        # Explicitly identify the most recent User message.
        # This helps resolve vague references such as "this", "that",
        # "it", and "more".
        recent_user_messages = [
            turn["content"]
            for turn in conversation_context
            if turn["role"] == "user"
        ]

        if recent_user_messages:
         history_block += (
        "Most recent User message:\n"
        f"{recent_user_messages[-1]}\n\n"
        "Reference resolution:\n"
        "If the current question uses a vague reference such as "
        "\"this\", \"that\", \"it\", \"these\", \"those\", or \"more\", "
        "treat the Most recent User message as the primary subject "
        "of that reference.\n"
        "Do not switch to an older topic unless the current question "
        "explicitly names that older topic.\n\n"
    )

    else:
        history_block = ""

    print("\n" + "=" * 60)
    print("DEBUG — SELECTED CONVERSATION CONTEXT")
    print("=" * 60)
    print(history_block)
    print("=" * 60 + "\n")

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
      context="",
      history_block=history_block,
      verified_evidence=verified_evidence,
      question=question,
    )

    return prompt, verified_evidence

# ============================================================
# GRANITE VIA OLLAMA
# ============================================================

def call_granite(prompt: str) -> str:

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": GRANITE_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": TEMPERATURE,
                    "num_predict": 256,
                },
            },
            timeout=120,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Couldn't reach Ollama at http://localhost:11434. "
            "Make sure Ollama is running."
        ) from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        ) from error

    try:
        data = response.json()

    except ValueError:
        return "[ERROR] Ollama returned invalid JSON."

    print(
        f"[PERFORMANCE] Ollama load duration: "
        f"{data.get('load_duration', 0) / 1_000_000_000:.3f}s"
    )

    print(
        f"[PERFORMANCE] Ollama prompt eval: "
        f"{data.get('prompt_eval_duration', 0) / 1_000_000_000:.3f}s"
    )

    print(
        f"[PERFORMANCE] Ollama generation: "
        f"{data.get('eval_duration', 0) / 1_000_000_000:.3f}s"
    )

    print(
        f"[PERFORMANCE] Ollama generated tokens: "
        f"{data.get('eval_count', 0)}"
    )

    answer = data.get(
        "response",
        "[ERROR] No response returned by Granite.",
    )

    print(
        f"[PERFORMANCE] Granite output characters: {len(answer)}"
    )

    return answer


# ============================================================
# PHASE 6 — EVIDENCE EXTRACTION
# ============================================================

EVIDENCE_EXTRACTION_PROMPT = """You are an evidence extraction assistant.

Your task is to extract only factual information that is explicitly
supported by the provided Wellness knowledge.

Rules:
- Use ONLY the provided Wellness knowledge.
- Extract factual information that is explicitly stated in the knowledge.
- The user's wording does NOT need to exactly match the wording in the
  knowledge.
- A clear paraphrase or semantically equivalent description may match
  a factual statement in the knowledge.
- If the user's wording describes a concept that is clearly represented
  by a factual statement in the knowledge, extract that factual statement
  from the knowledge.
- Prefer the wording of the knowledge rather than repeating or expanding
  the user's wording.
- If the question is only partially supported, extract ONLY the supported
  factual portion.
- Do not diagnose the user.
- Do not state that the user has a disorder, condition, or illness.
- Do not infer causes, diagnoses, severity, duration, or other facts
  about the user.
- Do not use pretrained knowledge.
- Do not add examples, symptoms, causes, treatments, definitions,
  durations, numbers, or recommendations that are not explicitly stated.
- If the knowledge does not contain information relevant to the question,
  output exactly:
  NO_SUPPORTED_EVIDENCE
- Keep the extracted evidence short and factual.
- Do not answer the user's question.
- Do not provide explanations beyond the extracted evidence.

Example of an allowed paraphrase:

Question:
"my mind wont stop racing with worry"

Knowledge:
"generalized anxiety disorder (persistent and excessive worry about
daily activities or events)"

Correct supported evidence:
"Generalized anxiety disorder involves persistent and excessive worry
about daily activities or events."

Incorrect:
"You have generalized anxiety disorder."

Incorrect:
"Racing thoughts mean you have generalized anxiety disorder."

The first is allowed because it extracts the factual statement from
the knowledge. The other two make an unsupported diagnosis or inference.

Example of unsupported evidence:

Question:
"what kinds of mental health problems are common in students"

Knowledge:
A passage that discusses stress management but does not list common
mental health problems in students.

Correct output:
NO_SUPPORTED_EVIDENCE

Wellness knowledge:
{context}

Question:
{question}

Supported evidence:
"""
# ============================================================
# PHASE 6 — EVIDENCE EXTRACTION FALLBACK
# ============================================================

EVIDENCE_EXTRACTION_FALLBACK_PROMPT = """You are a strict evidence
verification assistant.

A previous evidence extraction attempt returned:
NO_SUPPORTED_EVIDENCE

Re-check the Wellness knowledge below for a CLEAR factual statement
that directly supports any part of the user's question.

A clear paraphrase or semantically equivalent description counts as
support.

Rules:
- Use ONLY the provided Wellness knowledge.
- Do not use pretrained knowledge.
- Do not diagnose the user.
- Do not apply a disorder or condition to the user.
- Do not infer causes, severity, duration, or other facts.
- Extract ONLY a factual statement that is explicitly present in
  the knowledge.
- If the question contains multiple parts, extract only the part
  that is directly supported.
- Do not answer the user's question.
- Do not add recommendations or explanations.
- Prefer the wording of the knowledge.
- If there is no clear factual support, output exactly:
  NO_SUPPORTED_EVIDENCE

Question:
{question}

Wellness knowledge:
{context}

Supported evidence:
"""

def extract_supported_evidence(
    question: str,
    chunks: list,
) -> str:

    context_block = "\n\n".join(
        f"[{chunk['organization']} - {chunk['title']}]\n"
        f"{chunk['text']}"
        for chunk in chunks
    )

    # --------------------------------------------------------
    # FIRST EXTRACTION PASS
    # --------------------------------------------------------

    prompt = EVIDENCE_EXTRACTION_PROMPT.format(
        context=context_block,
        question=question,
    )

    evidence = call_granite(prompt).strip()

    if evidence != "NO_SUPPORTED_EVIDENCE":
        return evidence

    # --------------------------------------------------------
    # DETERMINISTIC EVIDENCE RECOVERY
    #
    # Used only when Granite incorrectly rejects evidence.
    #
    # IMPORTANT:
    # This recovery does not generate or paraphrase information.
    # It can only return an existing sentence from the retrieved
    # Wellness knowledge.
    # --------------------------------------------------------

    print(
        "[EVIDENCE EXTRACTION] "
        "Granite returned NO_SUPPORTED_EVIDENCE. "
        "Checking retrieved text for explicit phrase support."
    )

    question_lower = question.lower()

    # --------------------------------------------------------
    # HIGH-CONFIDENCE EVIDENCE RECOVERY
    #
    # This recovery is intentionally deterministic:
    # it may ONLY return text that already exists in retrieved
    # evidence. It does not generate or paraphrase evidence.
    # --------------------------------------------------------

    evidence_phrase_mappings = [
                # Sleep
        (
            [
                "fall asleep",
                "cannot sleep",
                "can't sleep",
                "trouble sleeping",
                "difficulty sleeping",
                "difficulty falling asleep",
                "hard to fall asleep",
                "harder to fall asleep",
                "unable to sleep",
                "lying awake in bed",
                "cannot sleep at night",
                "can't sleep at night",
            ],
            "fall asleep",
        ),

        # Panic/death wording.
        #
        # The user's wording "felt like I was dying" is not
        # lexically identical to the source wording "fear of
        # death or impending doom", so map the high-confidence
        # concepts explicitly.
        (
            [
                "felt like i was dying",
                "feel like i'm dying",
                "feel like i am dying",
                "feeling like i'm dying",
                "feeling like i am dying",
            ],
            [
                "fear of death",
                "impending doom",
            ],
        ),
        (
            [
                "fear of death",
                "impending doom",
            ],
            [
                "fear of death",
                "impending doom",
            ],
        ),
    ]

    # Find which evidence concepts are supported by the question.
    matched_evidence_phrases = []

    for question_phrases, evidence_phrases in evidence_phrase_mappings:
        if any(
            phrase in question_lower
            for phrase in question_phrases
        ):
            matched_evidence_phrases.extend(
                evidence_phrases
            )

    if not matched_evidence_phrases:
        return "NO_SUPPORTED_EVIDENCE"

    # --------------------------------------------------------
    # Return ONLY existing text from retrieved evidence.
    # Prefer the most specific evidence-containing segment.
    # --------------------------------------------------------

    best_sentence = None
    best_score = -1

    for chunk in chunks:
        text = chunk.get("text", "")

        sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            text,
        )

        for sentence in sentences:
            sentence_clean = sentence.strip()

            if not sentence_clean:
                continue

            sentence_lower = sentence_clean.lower()

            matched_phrases = [
                phrase
                for phrase in matched_evidence_phrases
                if phrase in sentence_lower
            ]

            if not matched_phrases:
                continue

            # Prefer longer/more specific evidence phrases.
            phrase_score = max(
                len(phrase)
                for phrase in matched_phrases
            )

            # Prefer substantive evidence sentences rather
            # than short headings or fragments.
            word_count = len(sentence_clean.split())

            score = phrase_score

            if word_count >= 8:
                score += 20

            if word_count >= 12:
                score += 10

            if score > best_score:
                best_score = score
                best_sentence = sentence_clean

    if best_sentence is not None:
        return best_sentence

    return "NO_SUPPORTED_EVIDENCE"

# ============================================================
# PHASE 6 — FINAL ANSWER VALIDATION
# ============================================================

def validate_generated_answer(
    question: str,
    answer: str,
    verified_evidence: str,
) -> str:

    """
    Deterministic safety boundary after Granite generation.

    The final answer must not:
    1. Apply a named disorder or condition to the individual user.
    2. Introduce factual Wellness information that is not present
       in the verified evidence.

    When a violation is detected, return the verified evidence itself.
    This is intentionally conservative: a shorter evidence-only answer
    is preferred over an unsupported generated answer.
    """

    answer_lower = answer.lower()
    evidence_lower = verified_evidence.lower()
    question_lower = question.lower()

    # --------------------------------------------------------
    # Diagnostic / condition names explicitly present in the
    # verified evidence.
    # --------------------------------------------------------

    diagnostic_terms = [
        "generalized anxiety disorder",
        "panic disorder",
        "panic attack",
        "major depressive disorder",
        "depression",
        "anxiety disorder",
        "eating disorder",
    ]

    matched_diagnoses = [
        term
        for term in diagnostic_terms
        if term in evidence_lower
        and term in answer_lower
    ]

    # --------------------------------------------------------
    # Determine whether the user is describing a personal
    # experience rather than asking for general information.
    # --------------------------------------------------------

    personal_question_patterns = [
        r"\bi\b",
        r"\bmy\b",
        r"\bme\b",
        r"\bive\b",
        r"\bi've\b",
        r"\bi'm\b",
        r"\bim\b",
        r"\bmyself\b",
    ]

    personal_question = any(
        re.search(
            pattern,
            question_lower,
        )
        for pattern in personal_question_patterns
    )

    # --------------------------------------------------------
    # Language that applies a named condition to the user.
    #
    # Includes direct diagnosis as well as softer diagnostic
    # phrasing such as "can be a symptom of" when referring
    # back to the user's individual experience.
    # --------------------------------------------------------

    personal_application_patterns = [
        "you have",
        "you may have",
        "you might have",
        "you could have",
        "you may be experiencing",
        "you might be experiencing",
        "you could be experiencing",
        "your symptoms",
        "your experience",
        "your description",
        "that experience",
        "this experience",
        "that description",
        "this description",
        "can be a symptom of",
        "may be a symptom of",
        "might be a symptom of",
        "could be a symptom of",
        "can indicate",
        "may indicate",
        "might indicate",
        "could indicate",
        "may be related to",
        "might be related to",
        "could be related to",
        "can be related to",
        "sounds like",
        "sounds consistent with",
        "is consistent with",
        "are consistent with",
        "suggestive of",
        "possibly",
        "possibly have",
    ]

    personal_application_detected = any(
        pattern in answer_lower
        for pattern in personal_application_patterns
    )

       # --------------------------------------------------------
    # If the user is describing a personal experience and the
    # generated answer introduces a named disorder/condition,
    # reject the generated answer.
    #
    # This intentionally does not depend on a particular wording
    # such as "sounds like", "symptom of", or "may have".
    # A generated answer can express the same unsafe relationship
    # in many different ways.
    # --------------------------------------------------------

    if (
        personal_question
        and matched_diagnoses
    ):

        print(
            "[ANSWER VALIDATION] "
            "Blocked named-condition application to personal question."
        )

        return (
              f"The available information says: {verified_evidence} "
             "However, it cannot determine what caused your individual experience "
             "or whether it was a specific condition."
)

    # --------------------------------------------------------
    # Personal sleep questions:
    #
    # If the verified evidence is an exact sleep-related source
    # statement, do not allow Granite to introduce broader claims
    # about sleep quality or outcomes.
    # --------------------------------------------------------

    sleep_expansion_patterns = [
        "improve sleep quality",
        "improves sleep quality",
        "better sleep quality",
        "improve your sleep",
        "improves your sleep",
        "sleep quality",
    ]

    if (
        personal_question
        and any(
            pattern in answer_lower
            for pattern in sleep_expansion_patterns
        )
        and "fall asleep" in evidence_lower
    ):

        print(
            "[ANSWER VALIDATION] "
            "Blocked unsupported sleep-related expansion."
        )

        return verified_evidence
    
    # --------------------------------------------------------
    # Evidence-boundary check.
    #
    # We only perform this check for answers that contain
    # factual Wellness material beyond the verified evidence.
    #
    # To avoid rejecting normal paraphrases, compare meaningful
    # content words rather than requiring exact sentence matches.
    # --------------------------------------------------------

    def normalize_words(text: str) -> set[str]:

        words = re.findall(
            r"\b[a-zA-Z][a-zA-Z'-]*\b",
            text.lower(),
        )

        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "can",
            "do",
            "for",
            "from",
            "has",
            "have",
            "if",
            "in",
            "into",
            "is",
            "it",
            "may",
            "of",
            "on",
            "or",
            "that",
            "the",
            "their",
            "them",
            "these",
            "this",
            "to",
            "was",
            "were",
            "what",
            "when",
            "which",
            "with",
            "you",
            "your",
        }

        return {
            word
            for word in words
            if word not in stop_words
            and len(word) > 2
        }

    evidence_words = normalize_words(
        verified_evidence
    )

    answer_words = normalize_words(
        answer
    )

    # --------------------------------------------------------
    # If the generated answer contains very little lexical
    # relationship to the verified evidence, prefer the
    # evidence itself.
    #
    # This is a conservative fallback, not a semantic proof
    # system. It mainly catches answers that have drifted into
    # unrelated pretrained knowledge.
    # --------------------------------------------------------

    if evidence_words and answer_words:

        overlap = (
            len(answer_words & evidence_words)
            / len(answer_words)
        )

        if overlap < 0.30:

            print(
                "[ANSWER VALIDATION] "
                "Generated answer has insufficient overlap "
                "with verified evidence."
            )

            return verified_evidence

    return answer

# ============================================================
# END-TO-END ANSWER
# ============================================================

def answer_query(
    vector_db,
    question: str,
    history: list | None = None,
) -> dict:

    total_start = time.perf_counter()

    # --------------------------------------------------------
    # STEP 1 — SAFETY
    # --------------------------------------------------------

    safety_start = time.perf_counter()

    safety_result = route_query(question)

    safety_time = time.perf_counter() - safety_start

    if safety_result["route"] != "normal":

        print("\n" + "=" * 60)
        print("PERFORMANCE")
        print("=" * 60)
        print(f"Safety: {safety_time:.3f}s")
        print(f"Total:  {time.perf_counter() - total_start:.3f}s")
        print("=" * 60 + "\n")

        # IMPORTANT:
        # Retrieval and Granite are completely bypassed.
        return {
            "route": safety_result["route"],
            "answer": safety_result["response"],
            "sources": [],
            "context_chunks": [],
        }

    # --------------------------------------------------------
    # STEP 2 — RETRIEVAL
    # --------------------------------------------------------

    retrieval_start = time.perf_counter()

    # Resolve conversation context before retrieval so that
    # contextual follow-up questions can retrieve against
    # the topic established by the previous user message.
    conversation_context = select_conversation_context(
        question,
        history,
    )

    retrieval_query = question
    previous_user_messages = []

    if conversation_context:
        previous_user_messages = [
            str(message.get("content", "")).strip()
            for message in conversation_context
            if message.get("role") == "user"
            and str(message.get("content", "")).strip()
        ]

    if previous_user_messages:
        retrieval_query = (
            f"{previous_user_messages[-1]} {question}"
        )

    print(
        f"[RETRIEVAL QUERY] {retrieval_query}"
    )

    retrieval_result = retrieve_context(
        vector_db,
        retrieval_query,
        k=TOP_K,
        candidate_k=CANDIDATE_K,
        max_per_source=MAX_PER_SOURCE,
    )

    if isinstance(retrieval_result, tuple):
       chunks, best_distance = retrieval_result
    else:
      # Backward-compatible path for existing tests/mocks
      # that return the original context-list format.
      chunks = retrieval_result
      best_distance = None

    retrieval_time = time.perf_counter() - retrieval_start

    if not chunks:

        print("\n" + "=" * 60)
        print("PERFORMANCE")
        print("=" * 60)
        print(f"Safety:     {safety_time:.3f}s")
        print(f"Retrieval:  {retrieval_time:.3f}s")
        print(f"Total:      {time.perf_counter() - total_start:.3f}s")
        print("=" * 60 + "\n")

        return {
            "route": "normal",
            "answer": (
                "I don't have enough information in my current "
                "knowledge base to answer that."
            ),
            "sources": [],
            "context_chunks": [],
        }

    # --------------------------------------------------------
    # STEP 2B — PHASE 6 EVIDENCE SUFFICIENCY GATE
    # --------------------------------------------------------
    
    if (
        best_distance is not None
        and best_distance > EVIDENCE_DISTANCE_THRESHOLD
    ):
        return {
            "route": "normal",
            "answer": (
                "I don't have enough information in my current "
                "knowledge base to answer that reliably."
            ),
            "sources": [],
            "context_chunks": [],
        }
    
    # --------------------------------------------------------
    # STEP 3 — PROMPT
    # --------------------------------------------------------

    prompt_start = time.perf_counter()

    prompt, verified_evidence = build_prompt(
        question,
        chunks,
        history,
    )

    print(
        f"[PERFORMANCE] Granite prompt characters: "
        f"{len(prompt)}"
    )

    prompt_time = time.perf_counter() - prompt_start

    # --------------------------------------------------------
    # STEP 3B — PHASE 6 VERIFIED EVIDENCE GATE
    # --------------------------------------------------------

    if verified_evidence == "NO_SUPPORTED_EVIDENCE":

        print(
            "[EVIDENCE GATE] No supported evidence. "
            "Skipping final Granite generation."
        )

        return {
            "route": "normal",
            "answer": (
                "I don't have enough information in my current "
                "knowledge base to answer that reliably."
            ),
            "sources": [],
            "context_chunks": [],
        }

    # --------------------------------------------------------
    # STEP 4 — GRANITE
    # --------------------------------------------------------

    ollama_start = time.perf_counter()

    answer = call_granite(prompt)

    ollama_time = time.perf_counter() - ollama_start

# --------------------------------------------------------
# STEP 4B — PHASE 6 DIAGNOSTIC APPLICATION VALIDATION
# --------------------------------------------------------

    validated_answer = validate_generated_answer(
    question,
    answer,
    verified_evidence,
)

    if validated_answer != answer:
      print(
        "[ANSWER VALIDATION] "
        "Blocked diagnostic application in generated answer."
    )

    answer = validated_answer

# --------------------------------------------------------
# STEP 5 — SOURCE LIST
# --------------------------------------------------------

    sources = []
    seen = set()

    for chunk in chunks:

        key = (
            chunk["organization"],
            chunk["title"],
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "organization": chunk["organization"],
                "title": chunk["title"],
            }
        )

    # --------------------------------------------------------
    # PERFORMANCE REPORT
    # --------------------------------------------------------

    total_time = time.perf_counter() - total_start

    print("\n" + "=" * 60)
    print("PERFORMANCE")
    print("=" * 60)
    print(f"Safety:          {safety_time:.3f}s")
    print(f"Retrieval:       {retrieval_time:.3f}s")
    print(f"Prompt:          {prompt_time:.3f}s")
    print(f"Ollama/Granite:  {ollama_time:.3f}s")
    print("-" * 60)
    print(f"TOTAL:           {total_time:.3f}s")
    print("=" * 60 + "\n")

    return {
        "route": "normal",
        "answer": answer,
        "sources": sources,
        "context_chunks": chunks,
    }


# ============================================================
# OUTPUT
# ============================================================

def print_result(result: dict):

    print("\n" + "=" * 60)
    print(f"ROUTE: {result['route']}")
    print("=" * 60)

    print("\nANSWER:")
    print(result["answer"])

    if result["sources"]:

        print("\nSOURCES:")

        for source in result["sources"]:
            print(
                f"  - {source['organization']}: "
                f"{source['title']}"
            )

    print()


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Wellness RAG query pipeline"
    )

    parser.add_argument(
        "--once",
        type=str,
        default=None,
        help="Answer one question and exit",
    )

    args = parser.parse_args()

    print("Loading Wellness RAG...")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Candidate pool: {CANDIDATE_K}")
    print(f"Final context chunks: {TOP_K}")
    print(f"Max chunks per source: {MAX_PER_SOURCE}")
    print(f"Granite model: {GRANITE_MODEL}")

    vector_db = get_vector_db()

    print("\nPipeline ready.\n")

    # --------------------------------------------------------
    # ONE QUESTION
    # --------------------------------------------------------

    if args.once:

        result = answer_query(
            vector_db,
            args.once,
        )

        print_result(result)
        return

    # --------------------------------------------------------
    # INTERACTIVE MODE
    # --------------------------------------------------------

    print(
        "Wellness RAG Bot\n"
        "Type a question or 'quit' to exit.\n"
    )

    while True:

        try:
            question = input("You: ").strip()

        except (EOFError, KeyboardInterrupt):

            print("\nExiting.")
            break

        if not question:
            continue

        if question.lower() in {
            "quit",
            "exit",
        }:
            break

        result = answer_query(
            vector_db,
            question,
        )

        print_result(result)


if __name__ == "__main__":
    sys.exit(main())