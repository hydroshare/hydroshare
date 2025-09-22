import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from pyld import jsonld

logger = logging.getLogger(__name__)

SCHEMA_VOCAB = {"@vocab": "https://schema.org/"}


def check_for_invalid_character(doc):
    """
    Returns a list of (path, message) issues. Empty list => OK.
    NOTE: This checks JSON-LD expandability only (no per-character filtering).
    """
    errors = []
    try:
        jsonld.expand(doc, options={"expandContext": SCHEMA_VOCAB})
    except Exception as e:
        errors.append(("$", f"Expansion failed: {e}"))
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

            print(f"🔄 Processing resource: {res.short_id} | {getattr(res.metadata, 'title', '') or ''}")
            resource_had_issue = False

            for funder in res.metadata.funding_agencies.all():
                agency_name = getattr(funder, "agency_name", "") or ""
                award_number = getattr(funder, "award_number", "") or ""

                # Build a minimal JSON-LD snippet for validation
                funder_jsonld = {
                    "@type": "Grant",
                    "funder": {"@type": "Organization", "name": agency_name},
                    "awardNumber": award_number,
                }

                issues = check_for_invalid_character(funder_jsonld)
                if issues:  # <-- non-empty => there IS a problem
                    if not resource_had_issue:
                        affected += 1
                        resource_had_issue = True
                    print(f"❌ JSON-LD issue in resource {res.short_id}:")
                    for path, msg in issues:
                        print(f"   • {path}: {msg}")

            count += 1

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Resources with issues: {affected} | Time taken: {total_duration}")
import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from pyld import jsonld

logger = logging.getLogger(__name__)

SCHEMA_VOCAB = {"@vocab": "https://schema.org/"}


def check_for_invalid_character(doc):
    """
    Returns a list of (path, message) issues. Empty list => OK.
    NOTE: This checks JSON-LD expandability only (no per-character filtering).
    """
    errors = []
    try:
        jsonld.expand(doc, options={"expandContext": SCHEMA_VOCAB})
    except Exception as e:
        errors.append(("$", f"Expansion failed: {e}"))
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

            print(f"🔄 Processing resource: {res.short_id} | {getattr(res.metadata, 'title', '') or ''}")
            resource_had_issue = False

            for funder in res.metadata.funding_agencies.all():
                agency_name = getattr(funder, "agency_name", "") or ""
                award_number = getattr(funder, "award_number", "") or ""

                # Build a minimal JSON-LD snippet for validation
                funder_jsonld = {
                    "@type": "Grant",
                    "funder": {"@type": "Organization", "name": agency_name},
                    "awardNumber": award_number,
                }

                issues = check_for_invalid_character(funder_jsonld)
                if issues:  # <-- non-empty => there IS a problem
                    if not resource_had_issue:
                        affected += 1
                        resource_had_issue = True
                    print(f"❌ JSON-LD issue in resource {res.short_id}:")
                    for path, msg in issues:
                        print(f"   • {path}: {msg}")

            count += 1

        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Resources with issues: {affected} | Time taken: {total_duration}")
