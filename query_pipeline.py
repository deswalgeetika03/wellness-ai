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
import sys
import re

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

OLLAMA_URL = "http://localhost:11434/api/generate"

# IMPORTANT:
# Change this if `ollama list` shows a different Granite model tag.
GRANITE_MODEL = "granite4.1:3b"

TEMPERATURE = 0.3


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT_TEMPLATE = """Role: You are a supportive wellness information assistant.

Task: Answer the user's question using the provided context.
You may apply or synthesize information from the context to the user's
situation, even when the context does not mention the user's exact
situation word-for-word. Do not introduce facts, treatments, numbers,
or recommendations that are not supported by the context.

Context:
{context}

Format:
Respond in 3-5 plain-language sentences.
Use clear, supportive language.
No unnecessary medical jargon.

Exclusions:
- Never diagnose, prescribe, recommend, select, or compare
  specific medications or dosages. If medication is relevant, state only
  that a qualified healthcare professional can discuss treatment options.

- Never diagnose or label the user's personal symptoms with a named
  mental-health disorder. Do not say that the user "has," "may have,"
  "might have," or "may be experiencing" a specific disorder based on
  symptoms they describe. Discuss disorders only as general educational
  information.

- Keep factual and medical claims grounded in the provided context.
  Do not add symptoms, causes, treatments, clinical details, or other
  factual claims that are not supported by the context.

- Avoid broad normalizing or reassuring statements about the user's
  personal symptoms, such as "this is completely normal" or "this is
  common," unless the provided context directly supports that framing.

- Never invent facts that are not present in the context.
- If the context does not contain enough information to answer the
  question, say so honestly. Do not invent missing information.
- Do not provide specific calorie, weight-loss, or meal-plan numbers.

Question:
{question}
"""


# ============================================================
# LOAD VECTOR DATABASE
# ============================================================

def get_vector_db():
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
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

    This directly addresses the observed imbalance where source 01
    represents 42.9% of the chunks in the database.
    """

    candidates = vector_db.similarity_search(
        question,
        k=candidate_k,
    )

    selected = []
    source_counts = {}

    # First pass:
    # Prefer one chunk from each source.
    for doc in candidates:
        source_id = str(doc.metadata.get("source_id", "?"))

        count = source_counts.get(source_id, 0)

        if count >= max_per_source:
            continue

        selected.append(doc)
        source_counts[source_id] = count + 1

        if len(selected) >= k:
            break

    # Fallback:
    # If there aren't enough distinct sources, fill remaining slots
    # using the original similarity ranking.
    if len(selected) < k:
        selected_ids = {id(doc) for doc in selected}

        for doc in candidates:
            if id(doc) in selected_ids:
                continue

            selected.append(doc)

            if len(selected) >= k:
                break

    return [
        {
            "text": doc.page_content,
            "source_id": str(doc.metadata.get("source_id", "?")),
            "title": doc.metadata.get("title", "Unknown source"),
            "organization": doc.metadata.get(
                "organization",
                "Unknown",
            ),
        }
        for doc in selected
    ]


# ============================================================
# PROMPT CONSTRUCTION
# ============================================================

def build_prompt(question: str, chunks: list) -> str:

    context_block = "\n\n".join(
        f"[{chunk['organization']} - {chunk['title']}]\n"
        f"{chunk['text']}"
        for chunk in chunks
    )

    return SYSTEM_PROMPT_TEMPLATE.format(
        context=context_block,
        question=question,
    )


# ============================================================
# GRANITE / OLLAMA
# ============================================================

def call_granite(prompt: str) -> str:

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": GRANITE_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE
                },
            },
            timeout=120,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        return (
            "[ERROR] Couldn't reach Ollama at "
            "http://localhost:11434.\n"
            "Make sure Ollama is running."
        )

    except requests.exceptions.RequestException as e:
        return f"[ERROR] Ollama request failed: {e}"

    try:
        data = response.json()
    except ValueError:
        return "[ERROR] Ollama returned invalid JSON."

    return data.get(
        "response",
        "[ERROR] No response returned by Granite.",
    )


# ============================================================
# END-TO-END ANSWER
# ============================================================

def answer_query(vector_db, question: str) -> dict:

    # --------------------------------------------------------
    # STEP 1 — SAFETY
    # --------------------------------------------------------

    safety_result = route_query(question)

    if safety_result["route"] != "normal":

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

    chunks = retrieve_context(
        vector_db,
        question,
        k=TOP_K,
        candidate_k=CANDIDATE_K,
        max_per_source=MAX_PER_SOURCE,
    )

    if not chunks:

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
    # STEP 3 — PROMPT
    # --------------------------------------------------------

    prompt = build_prompt(
        question,
        chunks,
    )

    # --------------------------------------------------------
    # STEP 4 — GRANITE
    # --------------------------------------------------------

    answer = call_granite(prompt)

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