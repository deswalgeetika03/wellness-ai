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

# Keep ChromaDB outside OneDrive (SQLite + background sync don't mix
# well). Update this path if your project lives somewhere else -
# but change it ONLY here, not in individual scripts.
CHROMA_DIR = Path(r"C:\Users\preet\Projects\wellness_chroma")

COLLECTION_NAME = "wellness_knowledge"

# Must be the SAME embedding model AND implementation used both to
# build the vector DB and to query it. Using LangChain's
# HuggingFaceEmbeddings consistently everywhere avoids accidentally
# mixing it with ChromaDB's separate built-in default embedding
# function (an ONNX export of the same base model, but not guaranteed
# to produce identical vectors).
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# The project's data folder is still fine to keep inside OneDrive/the
# repo - it's plain text/CSV, not a SQLite file being written to.
SOURCE_LOG_CSV = Path("data/source_log.csv")
CLEAN_DIR = Path("data/clean")