import re

from django.db.models import Q


from apps.legal_knowledge.models import LegalSection


def search_legal_sections(query, limit=5):
    """
    Search active legal provisions.

    Explicit references such as "Article 24" or
    "section 38" are prioritised before normal
    keyword-based retrieval.
    """
    query = (query or "").strip()

    if not query:
        return []

    explicit_numbers = re.findall(
        r"\b(?:article|section|sec(?:tion)?\.?)\s*"
        r"(\d+[A-Za-z]?)\b",
        query,
        flags=re.IGNORECASE,
    )

    exact_sections = []

    if explicit_numbers:
        exact_sections = list(
            LegalSection.objects.filter(
                section_number__in=explicit_numbers,
                is_active=True,
                document__is_active=True,
            )
            .select_related("document")
            .distinct()
        )

    stop_words = {
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "why",
        "how",
        "does",
        "about",
        "tell",
        "explain",
        "please",
        "constitution",
        "constitutional",
        "article",
        "articles",
        "section",
        "sections",
        "uganda",
        "ugandan",
        "law",
        "laws",
        "legal",
    }

    words = []

    for raw_word in query.split():
        word = raw_word.strip(
            ".,?!:;()[]{}\\\"'"
        ).lower()

        if (
            len(word) >= 4
            and not word.isdigit()
            and word not in stop_words
        ):
            words.append(word)

    scored_sections = []

    if words:
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

        exact_ids = {
            section.id
            for section in exact_sections
        }

        scored = []

        for section in sections:
            if section.id in exact_ids:
                continue

            searchable = (
                f"{section.heading} {section.text}"
            ).lower()

            score = sum(
                searchable.count(word)
                for word in words
            )

            if score > 0:
                scored.append(
                    (score, section)
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        scored_sections = [
            section
            for score, section in scored
        ]

    combined = exact_sections + scored_sections

    return combined[:limit]


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