from django.db.models import Q


from apps.legal_knowledge.models import LegalSection


def search_legal_sections(query, limit=5):
    """
    Simple first-pass legal retrieval.

    Searches constitutional article headings and text
    for words from the user's question.

    We can replace this later with embeddings/vector search.
    """
    query = (query or "").strip()

    if not query:
        return []

    words = [
        word.strip(".,?!:;()[]{}\"'").lower()
        for word in query.split()
        if len(word.strip(".,?!:;()[]{}\"'")) >= 4
    ]

    if not words:
        return []

    filters = Q()

    for word in words:
        filters |= Q(
            heading__icontains=word
        )
        filters |= Q(
            text__icontains=word
        )

    sections = (
        LegalSection.objects
        .filter(
            filters,
            is_active=True,
            document__is_active=True,
        )
        .select_related("document")
        .distinct()
    )

    scored = []

    for section in sections:
        searchable = (
            f"{section.heading} {section.text}"
        ).lower()

        score = sum(
            searchable.count(word)
            for word in words
        )

        scored.append(
            (score, section)
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        section
        for score, section in scored[:limit]
        if score > 0
    ]


def build_legal_context(sections):
    if not sections:
        return ""

    chunks = []

    for section in sections:
        chunks.append(
            "\n".join(
                [
                    (
                        f"Source: "
                        f"{section.document.title}"
                    ),
                    (
                        f"Article: "
                        f"{section.section_number}"
                    ),
                    (
                        f"Heading: "
                        f"{section.heading}"
                    ),
                    "Text:",
                    section.text,
                ]
            )
        )

    return "\n\n---\n\n".join(chunks)