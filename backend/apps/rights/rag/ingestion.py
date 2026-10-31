"""Document ingestion utilities for Sauti Yo's legal RAG knowledge base."""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[4]
LEGAL_SOURCES_DIR = PROJECT_ROOT / "legal_sources"


def load_legal_pdf(
    filename: str,
    *,
    title: str,
    category: str,
    version_date: str,
) -> list[Document]:
    """Load a legal PDF while preserving source and page metadata."""

    pdf_path = LEGAL_SOURCES_DIR / filename

    if not pdf_path.exists():
        raise FileNotFoundError(f"Legal source not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        if not text:
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "title": title,
                    "filename": filename,
                    "category": category,
                    "jurisdiction": "Uganda",
                    "authority": "primary_law",
                    "version_date": version_date,
                    "page": page_number,
                    "verified": True,
                },
            )
        )

    return documents


def split_legal_documents(
    documents: list[Document],
) -> list[Document]:
    """Split legal documents into retrieval-friendly overlapping chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return splitter.split_documents(documents)
