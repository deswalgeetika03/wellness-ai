import unittest
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

from rag_config import CHROMA_DIR, COLLECTION_NAME


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
# Retrieval Tests
# ---------------------------------------------------------

class TestRetrieval(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 60)
        print("WELLNESS RAG — RETRIEVAL REGRESSION TEST")
        print("=" * 60)

        print("\nLoading embedding model...")

        cls.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={
                "local_files_only": True
            },
            show_progress=False,
        )

        print("Embedding model loaded.")

        print("\nConnecting to ChromaDB...")

        cls.vector_db = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=cls.embeddings,
            persist_directory=str(CHROMA_DIR),
        )

        print("ChromaDB connected.")

    # -----------------------------------------------------
    # Test that every question returns results
    # -----------------------------------------------------

    def test_all_questions_return_results(self):

        for question in TEST_QUESTIONS:

            with self.subTest(question=question):

                results = self.vector_db.similarity_search(
                    question,
                    k=3,
                )

                self.assertEqual(
                    len(results),
                    3,
                    msg=f"Expected 3 results for: {question}",
                )

                print(
                    f"\n[PASS] Retrieved 3 chunks: "
                    f"{question}"
                )

    # -----------------------------------------------------
    # Test that retrieved documents contain metadata
    # -----------------------------------------------------

    def test_retrieved_documents_have_metadata(self):

        for question in TEST_QUESTIONS:

            with self.subTest(question=question):

                results = self.vector_db.similarity_search(
                    question,
                    k=3,
                )

                for document in results:

                    self.assertIsNotNone(
                        document.metadata,
                        msg=f"Missing metadata for: {question}",
                    )

                    self.assertTrue(
                        document.metadata.get("chunk_id"),
                        msg=f"Missing chunk_id for: {question}",
                    )

                    self.assertTrue(
                        document.metadata.get("organization"),
                        msg=f"Missing organization for: {question}",
                    )

                    self.assertTrue(
                        document.metadata.get("title"),
                        msg=f"Missing title for: {question}",
                    )

                    self.assertTrue(
                        document.metadata.get("filename"),
                        msg=f"Missing filename for: {question}",
                    )

        print(
            "\n[PASS] Retrieved documents contain "
            "required metadata"
        )

    # -----------------------------------------------------
    # Test that retrieved documents contain text
    # -----------------------------------------------------

    def test_retrieved_documents_have_content(self):

        for question in TEST_QUESTIONS:

            with self.subTest(question=question):

                results = self.vector_db.similarity_search(
                    question,
                    k=3,
                )

                for document in results:

                    self.assertTrue(
                        document.page_content.strip(),
                        msg=f"Empty document content for: {question}",
                    )

        print(
            "\n[PASS] Retrieved documents contain "
            "text content"
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)