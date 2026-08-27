import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pypdf import PdfReader

from apps.legal_knowledge.models import (
    LegalDocument,
    LegalSection,
)


ARTICLE_PATTERN = re.compile(
    r"^(\d{1,3}[A-Za-z]?)\.\s+(.+)$"
)

TOC_DOTS_PATTERN = re.compile(
    r"\.{4,}"
)


def clean_line(line):
    cleaned = " ".join(line.split()).strip()

    if not cleaned:
        return ""

    lower = cleaned.lower()

    # Remove recurring PDF footer/header text.
    if lower.startswith(
        "by ulii.org and laws.africa"
    ):
        return ""

    if lower in {
        "constitution of the republic of uganda uganda",
        "uganda constitution of the republic of uganda",
    }:
        return ""

    return cleaned


def looks_like_toc_heading(heading):
    """
    Table-of-contents headings contain long dotted leaders:
    Article title ............... page number
    """
    return bool(
        TOC_DOTS_PATTERN.search(heading)
    )


class Command(BaseCommand):
    help = (
        "Import the Constitution of Uganda from the "
        "local ULII PDF."
    )

    def add_arguments(self, parser):
        default_pdf = (
            Path(settings.BASE_DIR).parent
            / "legal_sources"
            / "uganda_constitution_2023.pdf"
        )

        parser.add_argument(
            "--pdf",
            type=str,
            default=str(default_pdf),
        )

        parser.add_argument(
            "--replace",
            action="store_true",
        )

    def handle(self, *args, **options):
        pdf_path = Path(
            options["pdf"]
        ).resolve()

        if not pdf_path.exists():
            raise CommandError(
                f"PDF not found: {pdf_path}"
            )

        self.stdout.write(
            f"Reading Constitution from: {pdf_path}"
        )

        reader = PdfReader(
            str(pdf_path)
        )

        self.stdout.write(
            f"PDF pages found: {len(reader.pages)}"
        )

        #
        # Collect every line together with its page.
        #

        all_lines = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            text = page.extract_text() or ""

            for raw_line in text.splitlines():
                line = clean_line(raw_line)

                if not line:
                    continue

                all_lines.append(
                    {
                        "page": page_number,
                        "text": line,
                    }
                )

        #
        # ---------------------------------------------------
        # FIND EVERY POSSIBLE ARTICLE OCCURRENCE
        # ---------------------------------------------------
        #
        # This deliberately allows duplicates because the
        # table of contents contains Article headings too.
        #

        candidates = []

        current = None

        def finish_candidate():
            nonlocal current

            if current is None:
                return

            body = "\n".join(
                current["lines"]
            ).strip()

            current["text"] = body
            candidates.append(current)

            current = None

        for item in all_lines:
            line = item["text"]
            match = ARTICLE_PATTERN.match(line)

            if match:
                number = match.group(1)
                heading = match.group(2).strip()

                #
                # A possible new Article.
                #
                finish_candidate()

                current = {
                    "number": number,
                    "heading": heading,
                    "page": item["page"],
                    "lines": [line],
                }

                continue

            if current is not None:
                current["lines"].append(line)

        finish_candidate()

        if not candidates:
            raise CommandError(
                "No possible Articles were detected."
            )

        #
        # ---------------------------------------------------
        # GROUP DUPLICATES AND PICK THE BEST VERSION
        # ---------------------------------------------------
        #

        by_number = {}

        for candidate in candidates:
            number = candidate["number"]

            by_number.setdefault(
                number,
                [],
            ).append(candidate)

        chosen_articles = []

        for number, versions in by_number.items():

            usable_versions = [
                candidate
                for candidate in versions
                if not looks_like_toc_heading(
                    candidate["heading"]
                )
            ]

            if not usable_versions:
                continue

            #
            # The actual constitutional Article will
            # normally contain much more text than its
            # table-of-contents entry.
            #
            best = max(
                usable_versions,
                key=lambda candidate: len(
                    candidate["text"]
                ),
            )

            #
            # Ignore suspiciously tiny matches.
            #
            if len(best["text"]) < 80:
                continue

            chosen_articles.append(best)

        if not chosen_articles:
            raise CommandError(
                "No substantive constitutional "
                "Articles were detected."
            )

        #
        # Sort Articles numerically, supporting 8A, 82A, etc.
        #

        def article_sort_key(article):
            match = re.match(
                r"^(\d+)([A-Za-z]?)$",
                article["number"],
            )

            if not match:
                return (9999, "")

            return (
                int(match.group(1)),
                match.group(2),
            )

        chosen_articles.sort(
            key=article_sort_key
        )

        article_map = {
            article["number"]: article
            for article in chosen_articles
        }

        #
        # ---------------------------------------------------
        # SAFETY VALIDATION
        # ---------------------------------------------------
        #

        expected_headings = {
            "1": "sovereignty",
            "20": "human rights",
            "21": "equality",
            "23": "personal liberty",
        }

        for number, expected in expected_headings.items():
            article = article_map.get(number)

            if article is None:
                raise CommandError(
                    f"Validation failed: "
                    f"Article {number} missing."
                )

            if expected not in article[
                "heading"
            ].lower():
                raise CommandError(
                    f"Validation failed: Article "
                    f"{number} heading is "
                    f"'{article['heading']}'"
                )

            if len(article["text"]) < 150:
                raise CommandError(
                    f"Validation failed: Article "
                    f"{number} contains too little text."
                )

        #
        # Extra check specifically for Article 21.
        #

        article_21_text = (
            article_map["21"]["text"].lower()
        )

        if (
            "all persons are equal"
            not in article_21_text
        ):
            raise CommandError(
                "Validation failed: Article 21 "
                "does not contain its substantive text."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Constitution validation passed."
            )
        )

        #
        # ---------------------------------------------------
        # CREATE DOCUMENT
        # ---------------------------------------------------
        #

        document, _ = (
            LegalDocument.objects.update_or_create(
                title=(
                    "Constitution of the Republic "
                    "of Uganda"
                ),
                defaults={
                    "short_title": (
                        "Constitution of Uganda"
                    ),
                    "document_type": "constitution",
                    "jurisdiction": "Uganda",
                    "source_name": (
                        "Uganda Legal Information "
                        "Institute (ULII)"
                    ),
                    "source_url": (
                        "https://ulii.org/en/akn/ug/"
                        "act/statute/1995/"
                        "constitution/"
                        "eng@2023-12-31"
                    ),
                    "version_date": date(
                        2023,
                        12,
                        31,
                    ),
                    "is_active": True,
                },
            )
        )

        if options["replace"]:
            deleted_count, _ = (
                document.sections.all().delete()
            )

            self.stdout.write(
                f"Removed {deleted_count} "
                "existing records."
            )

        #
        # ---------------------------------------------------
        # SAVE ARTICLES
        # ---------------------------------------------------
        #

        for order, article in enumerate(
            chosen_articles,
            start=1,
        ):
            LegalSection.objects.update_or_create(
                document=document,
                section_type="article",
                section_number=article[
                    "number"
                ],
                defaults={
                    "heading": article[
                        "heading"
                    ],
                    "text": article[
                        "text"
                    ],
                    "order": order,
                    "is_active": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported "
                f"{len(chosen_articles)} "
                "substantive constitutional Articles."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Constitution import complete."
            )
        )