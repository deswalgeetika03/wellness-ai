"""
rag_config.py

Single source of truth for paths and constants shared across the RAG
pipeline scripts (load_and_chunk.py, build_vector_db.py,
evaluate_retrieval.py, query_pipeline.py).

Import from here instead of redefining these values in more than one
place - that's exactly what caused the Chroma-path mismatch and the
duplicated/drifted source-metadata dict found during review.
"""

from pathlib import Path

# Keep ChromaDB outside the repository (SQLite files should not be
# committed or synchronized with the source tree). Override this path
# with WELLNESS_CHROMA_DIR when a different local location is needed.
import os

CHROMA_DIR = Path(
    os.getenv(
        "WELLNESS_CHROMA_DIR",
        str(Path.home() / "wellness_chroma"),
    )
)

COLLECTION_NAME = "wellness_knowledge"

# Must be the SAME embedding model AND implementation used both to
# build the vector DB and to query it. Using LangChain's
# HuggingFaceEmbeddings consistently everywhere avoids accidentally
# mixing it with ChromaDB's separate built-in default embedding
# function (an ONNX export of the same base model, but not guaranteed
# to produce identical vectors).
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# The project data folder contains source logs and cleaned text; the
# generated vector database is kept outside the repository.
SOURCE_LOG_CSV = Path("data/source_log.csv")
CLEAN_DIR = Path("data/clean")
