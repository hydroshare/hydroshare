# -*- coding: utf-8 -*-

"""
Use OpenAI to identify resources that are likely spam.
Reports suspected spam resources for admin review.
Does NOT automatically hide or modify any resource.

Usage:
    python manage.py ai_spam_resources
    python manage.py ai_spam_resources --discoverable --spam-only
    python manage.py ai_spam_resources --days 30 --output report.csv
    python manage.py ai_spam_resources --batch-size 20

Requires either:
  - OPENAI_API_KEY environment variable (OpenAI)
  - GITHUB_TOKEN environment variable (GitHub Models — free with GitHub Copilot)
"""

import csv
import os
import time

from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from hs_core.models import BaseResource
from hs_core import hydroshare


SYSTEM_PROMPT = (
    "You are a strict content moderation assistant for HydroShare, a data repository "
    "for anything related to water — including scientific research, water resource management, "
    "policy, education, engineering, environmental monitoring, and community water projects.\n\n"
    "Your task: identify submissions that are DEFINITELY spam or junk — not legitimate water-related content.\n\n"
    "SPAM examples (flag these):\n"
    "- Advertisements for products, services, pharmaceuticals, or software\n"
    "- SEO link spam or gibberish keyword stuffing\n"
    "- Adult content or escort services\n"
    "- Tech support scams, antivirus promotions, or device cleaner/optimizer tools\n"
    "- Hotel/travel booking promotions, cheap deal advertisements\n"
    "- Content with no plausible connection to water, hydrology, environment, or related fields\n\n"
    "LEGITIMATE examples (do NOT flag these):\n"
    "- Scientific datasets, models, and tools related to water or environmental topics\n"
    "- Water policy documents, management plans, or government reports\n"
    "- Educational materials, tutorials, or training data about water topics\n"
    "- Engineering reports, infrastructure data, or utility records\n"
    "- Community water monitoring, citizen science, or indigenous water knowledge\n"
    "- Resources in any language if the content appears water-related\n"
    "- Incomplete or poorly written abstracts that are still clearly water-related\n\n"
    "IMPORTANT: When in doubt, mark as LEGITIMATE. Only flag with HIGH confidence. "
    "A false negative (missing spam) is far less harmful than a false positive (hiding real content)."
)

# Categories used for classification
SPAM_CATEGORIES = (
    "EXTERNAL_SPAM",       # Commercial ads, essay services, travel packages, gaming accounts
    "TEST_DEV",            # Test/demo/debug resources from developers or staff
    "STUDENT_WORK",        # Class assignments, homework, course exercises
    "PLATFORM_INFRA",      # Logos, release notes, tool docs, conference presentations, software binaries
    "GEOGRAPHIC_PLACEHOLDER", # Empty resources with only a place name and no content
    "OFF_TOPIC",           # Legitimate content but unrelated to water (health, air, food, travel, etc.)
    "OTHER",               # Spam that doesn't fit the above categories
)

BATCH_PROMPT_TEMPLATE = (
    "Review the following {count} repository submissions from a water science data repository. "
    "For each, reply with exactly one of:\n"
    "  <index>|SPAM|HIGH|<category>|<one-sentence reason>   (only if highly confident it is spam)\n"
    "  <index>|LEGITIMATE\n\n"
    "Valid categories for SPAM:\n"
    "  EXTERNAL_SPAM       - commercial ads, essay services, travel/hotel promotions, gaming\n"
    "  TEST_DEV            - test/demo/debug resources from developers or staff\n"
    "  STUDENT_WORK        - class assignments, homework, course exercises\n"
    "  PLATFORM_INFRA      - logos, release notes, tool docs, conference presentations, software binaries\n"
    "  GEOGRAPHIC_PLACEHOLDER - only a place name, no meaningful content\n"
    "  OFF_TOPIC           - real content but unrelated to water (health, air pollution, food, etc.)\n"
    "  OTHER               - spam that doesn't fit above categories\n\n"
    "Do not flag anything unless you are certain. When uncertain, reply LEGITIMATE.\n\n"
    "{entries}"
)


def _build_entry(index, resource):
    """Build a text entry for a single resource to include in the LLM prompt."""
    title = ""
    abstract = ""
    keywords = []

    if resource.metadata:
        try:
            title = resource.metadata.title.value or ""
        except AttributeError:
            pass
        try:
            abstract = resource.metadata.description.abstract or ""
        except AttributeError:
            pass
        try:
            keywords = [s.value for s in resource.metadata.subjects.all()]
        except AttributeError:
            pass

    # Truncate abstract to keep token count manageable
    if len(abstract) > 500:
        abstract = abstract[:500] + "..."

    parts = [f"[{index}] Title: {title}"]
    if abstract:
        parts.append(f"    Abstract: {abstract}")
    if keywords:
        parts.append(f"    Keywords: {', '.join(keywords)}")
    return "\n".join(parts)


def _parse_response(response_text, batch_resources):
    """
    Parse the LLM response lines into a dict of {resource: (is_spam, category, reason)}.
    Expected format: <index>|SPAM|HIGH|<category>|<reason>  or  <index>|LEGITIMATE
    """
    results = {}
    for line in response_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 2:
            continue
        try:
            idx = int(parts[0].strip())
        except ValueError:
            continue
        if idx < 0 or idx >= len(batch_resources):
            continue
        verdict = parts[1].strip().upper()
        # Require HIGH confidence — skip if model didn't explicitly say HIGH
        if verdict == "SPAM":
            confidence = parts[2].strip().upper() if len(parts) > 2 else ""
            category = parts[3].strip().upper() if len(parts) > 3 else "OTHER"
            reason = parts[4].strip() if len(parts) > 4 else ""
            is_spam = confidence == "HIGH"
            if category not in SPAM_CATEGORIES:
                category = "OTHER"
        else:
            category = ""
            reason = ""
            is_spam = False
        results[batch_resources[idx]] = (is_spam, category, reason)
    return results


class Command(BaseCommand):
    help = "Use OpenAI to identify spam resources. Reports only — does not modify resources."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            dest='days',
            help='Only check resources updated in the last X days',
        )
        parser.add_argument(
            '--published',
            action='store_true',
            dest='published',
            help='Filter to only published resources',
        )
        parser.add_argument(
            '--public',
            action='store_true',
            dest='public',
            help='Filter to only public resources (raccess.public=True)',
        )
        parser.add_argument(
            '--discoverable',
            action='store_true',
            dest='discoverable',
            help='Filter to discoverable resources (includes public)',
        )
        parser.add_argument(
            '--discoverable-only',
            action='store_true',
            dest='discoverable_only',
            help='Filter to discoverable-but-NOT-public resources only (909 resources)',
        )
        parser.add_argument(
            '--private',
            action='store_true',
            dest='private',
            help='Filter to private resources only (not public, not discoverable)',
        )
        parser.add_argument(
            '--spam-only',
            action='store_true',
            dest='spam_only',
            help='Only print resources flagged as spam (suppress legitimate results)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            dest='batch_size',
            default=10,
            help='Number of resources to send per OpenAI API call (default: 10)',
        )
        parser.add_argument(
            '--output',
            type=str,
            dest='output',
            help='Optional path to write a CSV report (e.g. report.csv)',
        )
        parser.add_argument(
            '--model',
            type=str,
            dest='model',
            default='gpt-4o-mini',
            help='OpenAI model to use (default: gpt-4o-mini)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            dest='limit',
            default=None,
            help='Stop after checking this many resources (useful for testing)',
        )
        parser.add_argument(
            '--skip',
            type=int,
            dest='skip',
            default=0,
            help='Skip the first N resources (use with --limit to scan in daily chunks)',
        )
        parser.add_argument(
            '--append',
            action='store_true',
            dest='append',
            help='Append to an existing output CSV instead of overwriting it',
        )

    def handle(self, *args, **options):
        try:
            from openai import OpenAI
        except ImportError:
            raise CommandError(
                "The 'openai' package is not installed. "
                "Add it to the Docker image with: pip install openai"
            )

        openai_key = os.environ.get("OPENAI_API_KEY")
        github_token = os.environ.get("GITHUB_TOKEN")

        if openai_key:
            client = OpenAI(api_key=openai_key)
            self.stdout.write("Using OpenAI API.")
        elif github_token:
            client = OpenAI(
                api_key=github_token,
                base_url="https://models.inference.ai.azure.com",
            )
            self.stdout.write(
                "Using GitHub Models API (rate limit: ~150 req/day on free tier)."
            )
        else:
            raise CommandError(
                "No API key found. Set either:\n"
                "  OPENAI_API_KEY  — for OpenAI\n"
                "  GITHUB_TOKEN    — for GitHub Models (free with GitHub Copilot)"
            )

        days = options['days']
        published = options['published']
        public = options['public']
        discoverable = options['discoverable']
        discoverable_only = options['discoverable_only']
        private = options['private']
        spam_only = options['spam_only']
        batch_size = options['batch_size']
        output_path = options['output']
        model = options['model']
        limit = options['limit']
        skip = options['skip']
        append = options['append']

        site_url = hydroshare.utils.current_site_url()

        resources = BaseResource.objects.all()

        if discoverable_only:
            self.stdout.write("Filtering to discoverable-but-not-public resources only.")
            resources = resources.filter(raccess__discoverable=True, raccess__public=False)
        elif discoverable:
            self.stdout.write("Filtering to discoverable resources only.")
            resources = resources.filter(raccess__discoverable=True)
        if private:
            self.stdout.write("Filtering to private resources only.")
            resources = resources.filter(raccess__public=False, raccess__discoverable=False)
        if public:
            self.stdout.write("Filtering to public resources only.")
            resources = resources.filter(raccess__public=True)
        if published:
            self.stdout.write("Filtering to published resources only.")
            resources = resources.filter(raccess__published=True)
        if days:
            self.stdout.write(f"Filtering to resources updated in the last {days} days.")
            cutoff_time = timezone.now() - timedelta(days=days)
            resources = resources.filter(updated__gte=cutoff_time)

        resources = resources.order_by(F('updated').asc(nulls_first=True))
        total = resources.count()

        if total == 0:
            self.stdout.write("No resources found matching your filters.")
            return

        self.stdout.write(f"Checking {total} resources using model '{model}' (batch size: {batch_size})...\n")
        if skip:
            self.stdout.write(f"Skipping first {skip} resources (resuming from offset {skip}).\n")
        if limit:
            self.stdout.write(f"TEST MODE: stopping after {limit} resources.\n")

        spam_results = []
        checked = 0
        skipped = 0
        batch = []

        csv_file = None
        csv_writer = None
        if output_path:
            mode = "a" if append else "w"
            csv_file = open(output_path, mode, newline="", encoding="utf-8")
            csv_writer = csv.writer(csv_file)
            if not append:
                csv_writer.writerow(["short_id", "verdict", "category", "title", "reason", "url", "date_created", "owner_ids", "owner_usernames", "owner_emails", "owner_profile_urls"])

        try:
            for resource in resources.iterator():
                if skipped < skip:
                    skipped += 1
                    continue
                if limit and checked >= limit:
                    break
                batch.append(resource)
                if len(batch) >= batch_size:
                    spam_count = self._process_batch(
                        client, model, batch, site_url,
                        spam_only, spam_results, csv_writer
                    )
                    checked += len(batch)
                    self.stdout.write(
                        f"Progress: {checked}/{total} checked, {len(spam_results)} spam found so far."
                    )
                    batch = []
                    # Small delay to respect rate limits
                    time.sleep(0.5)

            # Process any remaining resources
            if batch:
                self._process_batch(
                    client, model, batch, site_url,
                    spam_only, spam_results, csv_writer
                )
                checked += len(batch)
        finally:
            if csv_file:
                csv_file.close()

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"Checked: {checked} | Suspected spam: {len(spam_results)}")
        self.stdout.write("=" * 70)

        if spam_results:
            self.stdout.write(f"\n{len(spam_results)} suspected spam resource(s):\n")
            for short_id, title, reason, url in spam_results:
                self.stdout.write(f"  [SPAM] {short_id} - \"{title}\"")
                self.stdout.write(f"         Reason: {reason}")
                self.stdout.write(f"         URL: {url}\n")

        if output_path:
            self.stdout.write(f"\nReport saved to: {output_path}")

        self.stdout.write(
            "\nNOTE: No resources were modified. Use the admin spam_allowlist view to act on results."
        )

    def _process_batch(self, client, model, batch, site_url, spam_only, spam_results, csv_writer):
        """Send a batch of resources to OpenAI and process the results."""
        entries = "\n\n".join(_build_entry(i, r) for i, r in enumerate(batch))
        prompt = BATCH_PROMPT_TEMPLATE.format(count=len(batch), entries=entries)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
        except Exception as e:
            self.stderr.write(f"OpenAI API error for batch: {e}")
            return 0

        response_text = response.choices[0].message.content
        results = _parse_response(response_text, batch)

        spam_count = 0
        for resource, (is_spam, category, reason) in results.items():
            title = ""
            if resource.metadata:
                try:
                    title = resource.metadata.title.value or ""
                except AttributeError:
                    pass
            url = site_url + resource.absolute_url

            try:
                owners = resource.raccess.owners.all()
                owner_ids = "|".join(str(o.id) for o in owners)
                owner_usernames = "|".join(o.username for o in owners)
                owner_emails = "|".join(o.email for o in owners)
                owner_profile_urls = "|".join(f"{site_url}/user/{o.id}/" for o in owners)
            except Exception:
                owner_ids = ""
                owner_usernames = ""
                owner_emails = ""
                owner_profile_urls = ""

            date_created = resource.created.strftime("%Y-%m-%d") if resource.created else ""

            if is_spam:
                spam_count += 1
                spam_results.append((resource.short_id, title, reason, url))
                self.stdout.write(f'[SPAM] {resource.short_id} - "{title}"')
                self.stdout.write(f'       Category: {category}')
                self.stdout.write(f'       Owner(s): {owner_usernames or "unknown"} — {owner_profile_urls}')
                self.stdout.write(f'       Reason: {reason}')
                self.stdout.write(f'       URL: {url}')
                if csv_writer:
                    csv_writer.writerow([resource.short_id, "SPAM", category, title, reason, url, date_created, owner_ids, owner_usernames, owner_emails, owner_profile_urls])
            elif not spam_only:
                self.stdout.write(f'[OK]   {resource.short_id} - "{title}"')
                if csv_writer:
                    csv_writer.writerow([resource.short_id, "LEGITIMATE", "", title, "", url, date_created, owner_ids, owner_usernames, owner_emails, owner_profile_urls])

        return spam_count
