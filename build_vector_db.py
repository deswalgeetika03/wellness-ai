from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from load_and_chunk import load_documents, split_documents
from rag_config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("WELLNESS RAG — BUILD VECTOR DATABASE")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. Load documents
    # -----------------------------------------------------

    print("\n[1/4] Loading documents...")

    documents = load_documents()

    print(
        f"Documents loaded: {len(documents)}"
    )

    # -----------------------------------------------------
    # 2. Create chunks
    # -----------------------------------------------------

    print("\n[2/4] Creating chunks...")

    chunks = split_documents(documents)

    print(
        f"Chunks created: {len(chunks)}"
    )

    if not chunks:
        print("\nERROR: No chunks found.")
        return

    # -----------------------------------------------------
    # 3. Load embedding model
    # -----------------------------------------------------

    print("\n[3/4] Loading embedding model...")

    print(
        f"Model: {EMBEDDING_MODEL}"
    )

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print("Embedding model loaded.")

    # -----------------------------------------------------
    # 4. Build / update ChromaDB
    # -----------------------------------------------------

    print("\n[4/4] Building ChromaDB...")

    CHROMA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=str(CHROMA_DIR),
    )

    # Stable IDs make the operation rebuild-safe (upsert on re-run
    # instead of duplicating chunks). Verified this by running the
    # script twice and confirming the collection count didn't grow -
    # see the note in README/report about this check.
    ids = [
        chunk.metadata["chunk_id"]
        for chunk in chunks
    ]

    print(
        f"Upserting {len(chunks)} chunks..."
    )

    vector_db.add_documents(
        documents=chunks,
        ids=ids,
    )

    print("\n" + "=" * 60)
    print("VECTOR DATABASE CREATED")
    print("=" * 60)

    print(
        f"Documents: {len(documents)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    print(
        f"Database: {CHROMA_DIR}"
    )

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    final_count = vector_db._collection.count()
    print(f"Collection count after upsert: {final_count}")
    if final_count != len(chunks):
        print(
            "[WARN] Collection count doesn't match chunk count - if you've "
            "run this script before, that's expected only if the chunk "
            "count itself changed (e.g. after editing load_and_chunk.py). "
            "If it's unexpectedly higher, IDs may not be upserting as "
            "intended - worth investigating before trusting retrieval."
        )

    print("\nVector database is ready.")


if __name__ == "__main__":
    main()