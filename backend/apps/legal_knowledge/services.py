import re

from django.db.models import Q

from apps.legal_knowledge.models import LegalSection


def _extract_explicit_references(query):
    """
    Return explicit legal references such as:
    Article 24, Section 38, or Sec. 12.

    The reference type is preserved so an Article cannot
    accidentally match a Section with the same number.
    """
    pattern = re.compile(
        r"\b("
        r"article|"
        r"section|"
        r"sec(?:tion)?\.?"
        r")\s*(\d+[A-Za-z]?)\b",
        flags=re.IGNORECASE,
    )

    references = []

    for reference_type, number in pattern.findall(query):
        normalized_type = reference_type.lower()

        if normalized_type.startswith("art"):
            section_type = "article"
        else:
            section_type = "section"

        references.append(
            {
                "section_type": section_type,
                "section_number": number,
            }
        )

    return references


def _document_query(query):
    """
    Build a document filter only when the user has actually
    identified a legal source.

    At present the Constitution is the only generic document
    reference that can be identified safely without knowing
    future Act names in advance.
    """
    normalized = query.lower()

    if (
        "constitution" in normalized
        or "constitutional" in normalized
    ):
        return (
            Q(document__document_type="constitution")
            | Q(document__title__icontains="constitution")
            | Q(document__short_title__icontains="constitution")
        )

    return None


def _find_exact_sections(query):
    """
    Resolve explicit Article/Section references safely.

    If the same explicit reference exists in more than one
    active legal document and the query does not identify a
    document, return no exact result rather than guessing.
    """
    references = _extract_explicit_references(query)

    if not references:
        return []

    document_filter = _document_query(query)
    exact_sections = []

    for reference in references:
        queryset = (
            LegalSection.objects
            .filter(
                section_type__iexact=reference[
                    "section_type"
                ],
                section_number__iexact=reference[
                    "section_number"
                ],
                is_active=True,
                document__is_active=True,
            )
            .select_related("document")
            .distinct()
        )

        if document_filter is not None:
            queryset = queryset.filter(document_filter)

        matches = list(queryset)

        document_ids = {
            section.document_id
            for section in matches
        }

        if (
            document_filter is None
            and len(document_ids) > 1
        ):
            # Ambiguous explicit reference. Do not guess
            # which legal document the user intended.
            continue

        exact_sections.extend(matches)

    return exact_sections


def search_legal_sections(query, limit=5):
    """
    Search active legal provisions.

    Explicit references such as "Article 24" or
    "Section 38" are prioritised before normal
    keyword-based retrieval.

    Explicit references are constrained by provision type.
    Ambiguous references across multiple legal documents
    are not guessed.
    """
    query = (query or "").strip()

    if not query:
        return []

    exact_sections = _find_exact_sections(query)

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
        reference_label = (
            section.section_type.capitalize()
            if section.section_type
            else "Provision"
        )

        chunks.append(
            "\n".join(
                [
                    (
                        f"Source: "
                        f"{section.document.title}"
                    ),
                    (
                        f"{reference_label}: "
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
