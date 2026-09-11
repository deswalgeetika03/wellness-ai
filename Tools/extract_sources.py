from pathlib import Path
import csv
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader
import ftfy


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")
SOURCE_LOG = Path("data/source_log.csv")


def clean_text(text: str) -> str:
    """Normalize extracted text without changing its meaning."""

    # Fix common UTF-8/Latin-1 encoding artifacts.
    text = ftfy.fix_text(text)

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Rejoin words split by a hyphen at a line break.
    # Example: "concentra-\ntion" -> "concentration"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # Normalize spaces within lines.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove whitespace at the beginning/end of each line.
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()


def extract_html(file_path: Path) -> str:
    """Extract readable text from an HTML file."""
    html = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "form"
    ]):
        element.decompose()

    main = soup.find("main")

    if main:
        text = main.get_text(separator="\n")
    else:
        text = soup.get_text(separator="\n")

    return clean_text(text)


def extract_pdf(file_path: Path) -> str:
    """Extract text from a PDF."""
    reader = PdfReader(str(file_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text:
            pages.append(
                f"[Page {page_number}]\n{text}"
            )

    return clean_text("\n\n".join(pages))


def process_file(file_path: Path, file_type: str) -> str:
    """Extract text based on source type."""

    if file_type.upper() == "HTML":
        return extract_html(file_path)

    if file_type.upper() == "PDF":
        return extract_pdf(file_path)

    raise ValueError(
        f"Unsupported file type: {file_type}"
    )


def main():
    CLEAN_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not SOURCE_LOG.exists():
        print(f"ERROR: Could not find {SOURCE_LOG}")
        return

    with SOURCE_LOG.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:
            source_id = row["ID"]
            filename = row["Local_Filename"]
            file_type = row["Type"]

            raw_path = RAW_DIR / filename

            if not raw_path.exists():
                print(
                    f"[SKIP] {source_id}: "
                    f"{filename} not found"
                )
                continue

            clean_filename = raw_path.stem + ".txt"
            clean_path = CLEAN_DIR / clean_filename

            print(
                f"[EXTRACT] {source_id}: "
                f"{filename}"
            )

            try:
                text = process_file(
                    raw_path,
                    file_type
                )

                if not text:
                    print(
                        "  WARNING: "
                        "No text extracted"
                    )
                    continue

                clean_path.write_text(
                    text,
                    encoding="utf-8"
                )

                print(
    f"  [OK] Saved {clean_path} "
    f"({len(text):,} characters)"
)

            except Exception as error:
                print(
                    f"  ERROR processing "
                    f"{filename}: {error}"
                )

    print("\nExtraction complete.")


if __name__ == "__main__":
    main()