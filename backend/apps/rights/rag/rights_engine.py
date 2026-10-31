"""Grounded Rights-to-Action generation for Sauti Yo."""

from django.conf import settings
from langchain_openai import ChatOpenAI

from apps.rights.rag.vector_store import search_legal_sources


SYSTEM_PROMPT = """
You are the Sauti Yo Rights-to-Action assistant for Uganda.

Your role is to explain rights information in clear, accessible language
using ONLY the verified legal context provided to you.

Rules:
1. Do not invent laws, sections, rights, institutions, deadlines, or procedures.
2. Do not rely on legal knowledge that is not present in the supplied context.
3. If the supplied context is insufficient, clearly say so.
4. Do not claim to be a lawyer and do not present the response as legal representation.
5. Clearly distinguish what the source says from practical general guidance.
6. Do not determine that a person is guilty, innocent, liable, or legally entitled
   to a particular outcome.
7. For immediate danger or urgent safety concerns, prioritise personal safety and
   appropriate emergency/support services.
8. Use plain English suitable for a member of the public.
9. Keep the answer practical and concise.
10. Preserve legal qualifications exactly. For example, if a right applies only
    when the detained person requests something, do not describe it as an
    unconditional right of the family.
11. Never strengthen, broaden, or simplify a legal rule in a way that changes
    its meaning.
12. When giving practical steps that are not expressly stated in the retrieved
    law, clearly present them as practical suggestions rather than legal rights.
13. Do not create a SOURCES USED section. Source attribution is added
    programmatically from the verified retrieved documents.
14. If the retrieved passages do not support a requested conclusion, say that
    the available verified sources are insufficient instead of guessing.
15. Do not assume that a dismissal is summary dismissal, unfair dismissal,
    wrongful dismissal, or another specific legal category unless the user's
    facts and retrieved context clearly support that classification.
16. When retrieved passages contain different complaint procedures, deadlines,
    remedies, or legal categories, state which conditions each one applies to.
    Do not combine them into one general rule.
17. Do not tell a user that a particular deadline applies to their situation
    unless the retrieved material clearly shows that the relevant legal
    procedure applies to the facts provided.
18. When the facts are insufficient to determine which legal procedure applies,
    explain the distinction and say what additional information would matter.
19. Treat legal deadlines as procedure-specific. Before stating a deadline,
    identify the retrieved provision that creates that deadline and the type of
    complaint to which it applies.
20. A deadline for summary dismissal must not be presented as the deadline for
    an ordinary dismissal, unfair dismissal, wrongful dismissal, or failure to
    provide a pre-dismissal hearing.
21. If the retrieved law provides a complaint route specifically for failure to
    follow the pre-dismissal hearing procedure, use that provision for a question
    about dismissal without an opportunity to respond rather than substituting
    the separate summary-dismissal procedure.

Return the response using exactly these headings:

WHAT THIS MAY INVOLVE

YOUR RIGHTS

WHAT YOU CAN DO NOW

INFORMATION OR EVIDENCE TO KEEP

WHEN TO SEEK FURTHER HELP

IMPORTANT NOTE
"""


def _format_context(documents) -> str:
    """Convert retrieved legal documents into attributed LLM context."""

    sections = []

    for number, document in enumerate(documents, start=1):
        metadata = document.metadata

        sections.append(
            f"""
SOURCE {number}
Title: {metadata.get("title")}
Jurisdiction: {metadata.get("jurisdiction")}
Version date: {metadata.get("version_date")}
PDF page: {metadata.get("page")}

LEGAL TEXT:
{document.page_content}
""".strip()
        )

    return "\n\n---\n\n".join(sections)


def _build_source_section(sources: list[dict]) -> str:
    """Build deterministic source attribution from retrieved metadata."""

    grouped = {}

    for source in sources:
        key = (
            source.get("title"),
            source.get("version_date"),
        )

        grouped.setdefault(key, set())

        if source.get("page") is not None:
            grouped[key].add(source["page"])

    lines = ["SOURCES USED", ""]

    for (title, version_date), pages in grouped.items():
        page_list = ", ".join(str(page) for page in sorted(pages))

        lines.append(
            f"- {title}, version {version_date}, PDF pages: {page_list}"
        )

    return "\n".join(lines)


def answer_rights_question(question: str, k: int = 8) -> dict:
    """Generate grounded rights-to-action guidance from verified legal sources."""

    question = question.strip()

    if not question:
        raise ValueError("A rights question is required.")

    documents = search_legal_sources(question, k=k)

    if not documents:
        return {
            "answer": (
                "I could not find enough verified legal information "
                "to answer this question safely."
            ),
            "sources": [],
        }

    context = _format_context(documents)

    llm = ChatOpenAI(
        model=settings.LLM_MODEL or "gpt-4.1-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )

    user_prompt = f"""
A user told Sauti Yo:

{question}

Use only the following retrieved Ugandan legal material to respond.

{context}
"""

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )

    sources = []

    for document in documents:
        metadata = document.metadata

        source = {
            "title": metadata.get("title"),
            "version_date": metadata.get("version_date"),
            "page": metadata.get("page"),
        }

        if source not in sources:
            sources.append(source)

    source_section = _build_source_section(sources)

    answer = response.content.strip()

    important_note_heading = "IMPORTANT NOTE"

    if important_note_heading in answer:
        before_note, note = answer.split(
            important_note_heading,
            maxsplit=1,
        )

        answer = (
            f"{before_note.rstrip()}\n\n"
            f"{source_section}\n\n"
            f"{important_note_heading}{note}"
        )
    else:
        answer = f"{answer}\n\n{source_section}"

    return {
        "answer": answer,
        "sources": sources,
    }
