import urllib.parse

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "List unknown funder names (names that are not in crossref funders registry for published resource(s)"

    def add_arguments(self, parser):

        # # a list of resource id's, or none to check all published resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        requests.packages.urllib3.disable_warnings()    # turn off SSL warnings

        def check_funder_name(funder_name):
            """Checks if the funder name exits in Crossref funders registry.
            Crossref API Documentation: https://api.crossref.org/swagger-ui/index.html#/Funders/get_funders
            """
            # url encode the funder name for the query parameter
            words = funder_name.split()
            # filter out words that contain the char '.'
            words = [word for word in words if '.' not in word]
            encoded_words = [urllib.parse.quote(word) for word in words]
            # match all words in the funder name
            query = "+".join(encoded_words)
            # if we can't find a match in first 50 search records then we are not going to find a match
            max_record_count = 50
            email = settings.DEFAULT_SUPPORT_EMAIL
            url = f"https://api.crossref.org/funders?query={query}&rows={max_record_count}&mailto={email}"
            funder_name = funder_name.lower()
            response = requests.get(url, verify=False)
            found_match = False
            error_msg = ""
            if response.status_code == 200:
                response_json = response.json()
                if response_json['status'] == 'ok':
                    items = response_json['message']['items']
                    for item in items:
                        if item['name'].lower() == funder_name:
                            found_match = True
                            return found_match, error_msg
                        for alt_name in item['alt-names']:
                            if alt_name.lower() == funder_name:
                                found_match = True
                                return found_match, error_msg
                    return found_match, error_msg
                return found_match, error_msg
            else:
                error_msg = "Failed to check funder_name: '{}' from Crossref funders registry. " \
                            "Status code: {}".format(funder_name, response.status_code)
                return found_match, error_msg

        def check_funders(funders, unmatched_res_counter):
            unmatched_funder_names = set()
            for funder in funders:
                funder_match, err_msg = check_funder_name(funder.agency_name)
                if err_msg:
                    print("-" * 100)
                    print(f"{err_msg} for resource: {resource.short_id}")
                    print("-" * 100)
                elif not funder_match:
                    unmatched_funder_names.add(funder.agency_name)
            if unmatched_funder_names:
                unmatched_res_counter += 1
                owners = resource.raccess.owners
                unmatched_names_str = "; ".join(unmatched_funder_names)
                owners_details = []
                for owner in owners:
                    owner_details = f"{owner.get_full_name() if owner.get_full_name() else owner.username}"
                    owner_details += f" ({owner.email})"
                    owners_details.append(owner_details)
                owners_details_str = ", ".join(owners_details)
                print(f"{res_counter}({unmatched_res_counter}). Resource:{resource.short_id},"
                      f" Unmatched funder names: {unmatched_names_str},"
                      f" Owners:{owners_details_str}")
            else:
                if funders:
                    print(f"{res_counter}. Resource:{resource.short_id} has all funder names matched")
                else:
                    print(f"{res_counter}. Resource:{resource.short_id} has no funder names")
            return unmatched_res_counter

        if len(options['resource_ids']) > 0:
            res_count = len(options['resource_ids'])
            print(f"TOTAL RESOURCES TO CHECK FOR FUNDER NAMES: {res_count}")
            print("=" * 100)
            res_counter = 0
            unmatched_res_counter = 0
            for res_id in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(res_id, or_404=False)
                    if not resource.raccess.published:
                        print(f"Resource:{res_id} is not a published resource")
                        continue
                except ObjectDoesNotExist:
                    print("No Resource found for id {}".format(res_id))
                    continue
                res_counter += 1
                funders = resource.metadata.funding_agencies.all()
                unmatched_res_counter = check_funders(funders, unmatched_res_counter)
        else:
            # check all published resources
            res_count = BaseResource.objects.filter(raccess__published=True).count()
            print(f"TOTAL PUBLISHED RESOURCES TO CHECK FOR FUNDER NAMES: {res_count}")
            print("=" * 100)
            res_counter = 0
            unmatched_res_counter = 0
            for resource in BaseResource.objects.filter(raccess__published=True):
                res_counter += 1
                resource = resource.get_content_model()
                funders = resource.metadata.funding_agencies.all()
                unmatched_res_counter = check_funders(funders, unmatched_res_counter)