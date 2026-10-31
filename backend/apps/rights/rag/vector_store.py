"""Vector-store utilities for Sauti Yo's verified legal knowledge base."""

from pathlib import Path

from django.conf import settings
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from apps.rights.rag.ingestion import load_legal_pdf, split_legal_documents


BACKEND_ROOT = Path(__file__).resolve().parents[3]
VECTOR_STORE_DIR = BACKEND_ROOT / "data" / "legal_vector_store"


LEGAL_SOURCES = [
    {
        "filename": "uganda_constitution_2023.pdf",
        "title": "Constitution of the Republic of Uganda",
        "category": "constitutional_rights",
        "version_date": "2023-12-31",
    },
    {
        "filename": "uganda_employment_act_2026.pdf",
        "title": "Employment Act, Chapter 226",
        "category": "employment_rights",
        "version_date": "2026-06-05",
    },
]


def get_embeddings() -> OpenAIEmbeddings:
    """Return the embedding model used for legal semantic search."""

    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. "
            "Add it to the Sauti Yo environment before building the index."
        )

    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
    )


def build_legal_index() -> FAISS:
    """Build one searchable FAISS index from all verified legal sources."""

    all_chunks = []

    for source in LEGAL_SOURCES:
        documents = load_legal_pdf(
            source["filename"],
            title=source["title"],
            category=source["category"],
            version_date=source["version_date"],
        )

        chunks = split_legal_documents(documents)
        all_chunks.extend(chunks)

        print(
            f'Loaded {source["title"]}: '
            f'{len(documents)} pages -> {len(chunks)} chunks'
        )

    if not all_chunks:
        raise RuntimeError("No legal documents were available for indexing.")

    vector_store = FAISS.from_documents(
        all_chunks,
        get_embeddings(),
    )

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(VECTOR_STORE_DIR))

    print(f"Total indexed chunks: {len(all_chunks)}")

    return vector_store


def build_constitution_index() -> FAISS:
    """Backward-compatible alias for rebuilding the complete legal index."""

    return build_legal_index()


def load_vector_store() -> FAISS:
    """Load Sauti Yo's persisted legal vector index."""

    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            "Legal vector index does not exist. Build it first."
        )

    return FAISS.load_local(
        str(VECTOR_STORE_DIR),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def _source_config(filename: str):
    """Return configuration metadata for an indexed legal source."""

    return next(
        (
            source
            for source in LEGAL_SOURCES
            if source["filename"] == filename
        ),
        None,
    )


def _load_neighboring_pages(document, radius: int = 1):
    """Load adjacent pages from the same verified legal source.

    Legal provisions often continue across PDF page boundaries. Including
    neighboring pages helps preserve qualifications, complaint procedures,
    deadlines, and remedies that belong to the retrieved provision.
    """

    metadata = document.metadata
    filename = metadata.get("filename")
    page = metadata.get("page")

    if not filename or not isinstance(page, int):
        return []

    source = _source_config(filename)

    if source is None:
        return []

    pages = load_legal_pdf(
        filename,
        title=source["title"],
        category=source["category"],
        version_date=source["version_date"],
    )

    minimum_page = max(1, page - radius)
    maximum_page = page + radius

    return [
        candidate
        for candidate in pages
        if minimum_page <= candidate.metadata.get("page", 0) <= maximum_page
    ]


def search_legal_sources(
    query: str,
    k: int = 4,
    *,
    include_neighbors: bool = True,
):
    """Retrieve relevant legal text with nearby page context.

    Semantic search identifies the strongest passages. Neighboring pages are
    then included because statutory sections may cross PDF page boundaries.
    """

    vector_store = load_vector_store()
    matches = vector_store.similarity_search(query, k=k)

    if not include_neighbors:
        return matches

    documents = []
    seen = set()

    for match in matches:
        candidates = [match, *_load_neighboring_pages(match)]

        for candidate in candidates:
            metadata = candidate.metadata

            identity = (
                metadata.get("filename"),
                metadata.get("page"),
                candidate.page_content,
            )

            if identity in seen:
                continue

            seen.add(identity)
            documents.append(candidate)

    return documents
