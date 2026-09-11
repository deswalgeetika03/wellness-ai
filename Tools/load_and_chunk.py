import csv
from pathlib import Path
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_config import CLEAN_DIR, SOURCE_LOG_CSV

# Source 07 is safety-layer-only.
SAFETY_ONLY_IDS = {"07"}

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# ---------------------------------------------------------
# Source metadata - loaded from source_log.csv, NOT hardcoded here.
# source_log.csv is the single source of truth for organization/title
# (it's also your report's citation chapter) - keeping a second,
# hand-typed copy in this file is exactly how titles drift out of sync
# between what gets cited in the report and what gets shown to users.
# ---------------------------------------------------------

def load_source_metadata(csv_path: Path = SOURCE_LOG_CSV) -> dict:
    """Load {source_id: {organization, title}} from source_log.csv.

    IDs are zero-padded to 2 digits on load. This matters because
    opening/saving source_log.csv in Excel silently strips leading
    zeros from text-looking numeric cells (e.g. "01" becomes "1")
    unless that column is explicitly formatted as text - which is
    exactly what happened here and caused every source 01-09 to fall
    back to "Unknown" metadata. Normalizing on load means that if it
    happens again, this code recovers instead of failing silently.
    """
    metadata = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            source_id = row["ID"].strip().zfill(2)
            metadata[source_id] = {
                "organization": row["Organization"],
                "title": row["Title"],
            }
    return metadata


SOURCE_METADATA = load_source_metadata()


def clean_text(text: str) -> str:
    """Clean extracted text while preserving its meaning."""

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Rejoin words split by a hyphen at a line break.
    # Example:
    # concentra-
    # tion
    # becomes:
    # concentration
    text = re.sub(
        r"(\w)-\s*\n\s*(\w)",
        r"\1\2",
        text
    )

    # Normalize spaces.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove whitespace around lines.
    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    text = "\n".join(lines)

    return text.strip()


def get_source_id(filename: str) -> str:
    """Extract the two-digit source ID from the filename."""
    return Path(filename).stem[:2]


def load_documents() -> list[Document]:
    """Load cleaned text files and attach source metadata."""

    documents = []

    for file_path in sorted(CLEAN_DIR.glob("*.txt")):

        source_id = get_source_id(file_path.name)

        # Safety source is deliberately excluded
        # from general RAG retrieval.
        if source_id in SAFETY_ONLY_IDS:
            print(
                f"[EXCLUDE] {file_path.name} "
                f"(safety-layer-only)"
            )
            continue

        raw_text = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        text = clean_text(raw_text)

        if not text:
            print(
                f"[SKIP] {file_path.name} "
                f"is empty"
            )
            continue

        metadata = SOURCE_METADATA.get(
            source_id,
            {
                "organization": "Unknown",
                "title": file_path.stem,
            }
        )
        if source_id not in SOURCE_METADATA:
            print(
                f"[WARN] {file_path.name} has source_id={source_id!r} "
                f"not found in source_log.csv - using fallback metadata. "
                f"Check for a typo or missing row."
            )

        document = Document(
            page_content=text,
            metadata={
                "source_id": source_id,
                "organization": metadata["organization"],
                "title": metadata["title"],
                "filename": file_path.name,
                "source_path": str(file_path),
            },
        )

        documents.append(document)

        print(
            f"[LOAD] {file_path.name} "
            f"({len(text):,} characters)"
        )

    return documents


def split_documents(
    documents: list[Document],
) -> list[Document]:
    """Split documents into retrieval-sized chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(documents)

    # Create stable chunk IDs within each source. Prefixed with
    # source_id, so IDs are unique ACROSS the whole dataset, not just
    # within one source - this matters because build_vector_db.py uses
    # these as the Chroma document IDs directly, and a collision there
    # would silently overwrite one chunk with another.
    source_counts = {}

    for chunk in chunks:

        source_id = chunk.metadata["source_id"]

        source_counts[source_id] = (
            source_counts.get(source_id, 0) + 1
        )

        chunk.metadata["chunk_id"] = (
            f"{source_id}_"
            f"{source_counts[source_id]:04d}"
        )

    return chunks


def main():

    print("=" * 60)
    print("WELLNESS RAG — DOCUMENT LOADING & CHUNKING")
    print("=" * 60)

    documents = load_documents()

    print("\n" + "-" * 60)
    print(
        f"Documents loaded: "
        f"{len(documents)}"
    )

    chunks = split_documents(documents)

    print(
        f"Chunks created: "
        f"{len(chunks)}"
    )

    if not chunks:
        print(
            "\nERROR: "
            "No chunks were created."
        )
        return

    chunk_lengths = [
        len(chunk.page_content)
        for chunk in chunks
    ]

    small_chunks = [
        length
        for length in chunk_lengths
        if length < 50
    ]

    short_chunks = [
        chunk
        for chunk in chunks
        if len(chunk.page_content) < 50
    ]

    average_length = (
        sum(chunk_lengths)
        / len(chunk_lengths)
    )

    print(
        f"Average chunk size: "
        f"{average_length:.0f} characters"
    )

    print(
        f"Smallest chunk: "
        f"{min(chunk_lengths)} characters"
    )

    print(
        f"Largest chunk: "
        f"{max(chunk_lengths)} characters"
    )

    print(
        f"Chunks under 50 characters: "
        f"{len(small_chunks)}"
    )
    print("\n" + "-" * 60)
    print("SHORT CHUNKS (<50 CHARACTERS)")
    print("-" * 60)

    for chunk in short_chunks:
        print(
            f"\n[{chunk.metadata['chunk_id']}] "
            f"{chunk.metadata['organization']} — "
            f"{chunk.metadata['title']}"
        )
        print(repr(chunk.page_content))

    # -----------------------------------------------------
    # Metadata verification
    # -----------------------------------------------------

    print("\n" + "-" * 60)
    print("METADATA CHECK")
    print("-" * 60)

    for chunk in chunks[:3]:

        print(
            f"\nChunk ID: "
            f"{chunk.metadata['chunk_id']}"
        )

        print(
            f"Organization: "
            f"{chunk.metadata['organization']}"
        )

        print(
            f"Title: "
            f"{chunk.metadata['title']}"
        )

        print(
            f"Filename: "
            f"{chunk.metadata['filename']}"
        )

    # -----------------------------------------------------
    # Sample chunks
    # -----------------------------------------------------

    print("\n" + "-" * 60)
    print("SAMPLE CHUNKS")
    print("-" * 60)

    for chunk in chunks[:3]:

        print(
            f"\n[{chunk.metadata['chunk_id']}] "
            f"{chunk.metadata['filename']}"
        )

        print("-" * 40)

        print(
            chunk.page_content[:500]
        )

    print("\n" + "=" * 60)
    print("Chunking complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()