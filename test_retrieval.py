from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHROMA_DIR = Path(
    r"C:\Users\preet\Projects\wellness_chroma"
)

COLLECTION_NAME = "wellness_knowledge"


# ---------------------------------------------------------
# Questions to test
# ---------------------------------------------------------

TEST_QUESTIONS = [
    "How can I deal with stress before exams?",
    "What are common symptoms of anxiety?",
    "What is a panic attack?",
    "How can I improve my sleep?",
    "What are common types of eating disorders?",
]


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("WELLNESS RAG — RETRIEVAL TEST")
    print("=" * 60)

    print("\nLoading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    print("Embedding model loaded.")

    print("\nConnecting to ChromaDB...")

    vector_db = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    print("ChromaDB connected.")

    # -----------------------------------------------------
    # Test each question
    # -----------------------------------------------------

    for question in TEST_QUESTIONS:

        print("\n" + "=" * 60)
        print("QUESTION")
        print("=" * 60)

        print(question)

        print("\nTOP 3 RETRIEVED CHUNKS")
        print("-" * 60)

        results = vector_db.similarity_search(
            question,
            k=3,
        )

        for rank, document in enumerate(
            results,
            start=1
        ):

            metadata = document.metadata

            print(
                f"\n[{rank}] "
                f"{metadata.get('chunk_id')}"
            )

            print(
                f"Source: "
                f"{metadata.get('organization')}"
            )

            print(
                f"Title: "
                f"{metadata.get('title')}"
            )

            print(
                f"File: "
                f"{metadata.get('filename')}"
            )

            print("\nText:")

            print(
                document.page_content[:500]
            )

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()