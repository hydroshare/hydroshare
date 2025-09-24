import logging
import time
import unicodedata

from datetime import timedelta
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from pyld import jsonld

logger = logging.getLogger(__name__)

SCHEMA_VOCAB = {"@vocab": "https://schema.org/"}


def _scan_ecma_string_issues(value, path="$"):
    """
    Recursively scan a Python object (dict/list/str/etc.) and yield
    (path, message) for ECMA-262 JSON string incompatibilities.

    Rules enforced:
      - Control chars U+0000..U+001F are not allowed unescaped in JSON strings.
      - The quotation mark (U+0022, ") and reverse solidus (U+005C)
        must be escaped in JSON strings. We flag presence so callers can escape.
      - Lone UTF-16 surrogate code points U+D800..U+DFFF are invalid Unicode.
    """
    if isinstance(value, dict):
        for k, v in value.items():
            k_path = f'{path}["{k}"]'
            yield from _scan_ecma_string_issues(v, k_path)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            i_path = f"{path}[{i}]"
            yield from _scan_ecma_string_issues(v, i_path)
    elif isinstance(value, str):
        # Check each code point
        for idx, ch in enumerate(value):
            cp = ord(ch)

            # 1) Control characters U+0000..U+001F
            if 0x00 <= cp <= 0x1F:
                name = unicodedata.name(ch, "CONTROL")
                yield (
                    path,
                    f"Control char {name} (U+{cp:04X}) at index {idx} must be escaped in JSON."
                )

            # 2) Lone surrogate (invalid scalar value)
            if 0xD800 <= cp <= 0xDFFF:
                yield (
                    path,
                    f"Lone surrogate codepoint U+{cp:04X} at index {idx} is invalid Unicode for JSON."
                )

            # 3) Characters that must be escaped: quotation mark and reverse solidus
            if ch == '"':
                yield (
                    path,
                    f'Quotation mark U+0022 (") at index {idx} must be escaped as \\" in JSON.'
                )
            if ch == '\\':
                yield (
                    path,
                    r"Reverse solidus U+005C (\) at index {idx} must be escaped as \\ in JSON."
                )

        # (FYI: solidus '/' does not need escaping; it *may* be escaped but is valid as-is.)

    else:
        # Numbers, bools, None are fine.
        return


def check_for_invalid_character(doc):
    """
    Returns a list of (path, message) issues. Empty list => OK.

    First, validates that all string values in `doc` comply with ECMA-262 JSON
    string constraints (control chars, required escapes, lone surrogates).
    Then, attempts JSON-LD expansion as an additional structural check.
    """
    errors = []

    # ECMA-262 JSON string scan (content-level)
    for path, msg in _scan_ecma_string_issues(doc, path="$"):
        errors.append((path, msg))

    # JSON-LD expandability (structure-level)
    try:
        jsonld.expand(doc, options={"expandContext": SCHEMA_VOCAB})
    except Exception as e:
        errors.append(("$", f"JSON-LD expansion failed: {e}"))

    return errors


class Command(BaseCommand):
    help = "Find all published resources with JSON-LD expandability issues in funding metadata."

    def handle(self, *args, **options):
        start_time = time.time()
        published_resources = BaseResource.public_resources.filter(raccess__published=True)

        total = published_resources.count()
        print(f"📦 Total published resources to process: {total}")
        count = 0
        affected = 0

        for res in published_resources.iterator():
            res = res.get_content_model()
            if not getattr(res, "metadata", None):
                logger.warning(f"Resource {res.short_id} has no metadata. Skipping.")
                continue

            resource_had_issue = False
            error_messages = []

            for funder in res.metadata.funding_agencies.all():
                agency_name = getattr(funder, "agency_name", "") or ""
                award_number = getattr(funder, "award_number", "") or ""

                funder_jsonld = {
                    "@type": "Grant",
                    "funder": {"@type": "Organization", "name": agency_name},
                    "awardNumber": award_number,
                }

                issues = check_for_invalid_character(funder_jsonld)
                if issues:
                    if not resource_had_issue:
                        affected += 1
                        resource_had_issue = True
                    # Collect all issues for this resource
                    for path, msg in issues:
                        error_messages.append(f"{path}: {msg}")

            count += 1

            if error_messages:
                # Print everything in one line: ID | Title | Errors
                title = getattr(res.metadata, "title", "") or ""
                print(f"❌ Invalid Character found for resource with id {res.short_id} and Title {title}"
                      f" | {' || '.join(error_messages)}")

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | "
              f"Affected Resources: {affected} | Time taken: {total_duration}")
