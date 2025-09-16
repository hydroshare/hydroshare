import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand

from hs_core.models import BaseResource

logger = logging.getLogger(__name__)


def check_for_invalid_character(s):
    return all(
        0x20 <= ord(c) <= 0x7E and c not in {'"', "'", '<', '>', '\\'}
        for c in s
    )


class Command(BaseCommand):
    help = "Migrate all resources from Crossref to DataCite"

    def handle(self, *args, **options):
        start_time = time.time()
        published_resources = BaseResource.public_resources.filter(raccess__published=True)

        total = published_resources.count()
        print(f"📦 Total published resources to process: {total}")
        count = 0

        for res in published_resources.iterator():
            res = res.get_content_model()
            if not res.metadata:
                logger.warning(f"Resource {res.short_id} has no metadata. Skipping.")
                continue
            # if count < 30:
            #     count += 1
            #     continue
            print(f"🔄 Processing resource: {res.short_id} | {res.metadata.title}")
            for funder in res.metadata.funding_agencies.all():
                if not check_for_invalid_character(funder.agency_name):
                    print(f"❌ Invalid character found in agency name: {funder.agency_name} | "
                          "Resource: {res.short_id}")
                if not check_for_invalid_character(funder.award_number):
                    print(f"❌ Invalid character found in award number: {funder.award_number} | "
                          "Resource: {res.short_id}")
            # res_start_time = time.time()
            # res_duration = timedelta(seconds=int(time.time() - res_start_time))
            # print(f"✅ Finished processing resource: {res.short_id} | {res.metadata.title} | "
            # "Time taken: {res_duration}")
            # count += 1
            # if count == 130:
            #     break
            # break  # Remove this break to process all resources
        total_duration = timedelta(seconds=int(time.time() - start_time))
        print(f"🎉 Finished processing {count} resources | Time taken: {total_duration}")
