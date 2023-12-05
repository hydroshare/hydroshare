import requests
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
            query = "+".join(funder_name.split())
            # if we can't find a match in first 50 search records then we are not going to find a match
            max_record_count = 50
            url = f"https://api.crossref.org/funders?query={query}&rows={max_record_count}"
            funder_name = funder_name.lower()
            response = requests.get(url, verify=False)
            found_match = False
            if response.status_code == 200:
                response_json = response.json()
                if response_json['status'] == 'ok':
                    items = response_json['message']['items']
                    for item in items:
                        if item['name'].lower() == funder_name:
                            found_match = True
                            return found_match
                        for alt_name in item['alt-names']:
                            if alt_name.lower() == funder_name:
                                found_match = True
                                return found_match
                    return found_match
                return found_match
            else:
                msg = "Failed to check funder_name: {} from Crossref funders registry. " \
                      "Status code: {}".format(funder_name, response.status_code)
                print(msg)
                return found_match

        if len(options['resource_ids']) > 0:
            res_count = len(options['resource_ids'])
            print(f"TOTAL RESOURCES TO CHECK FOR FUNDER NAMES: {res_count}")
            print("=" * 100)
            for res_id in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(res_id, or_404=False)
                    if not resource.raccess.published:
                        print(f"Resource:{res_id} is not a published resource")
                        continue
                except ObjectDoesNotExist:
                    print("No Resource found for id {}".format(res_id))
                    continue
                funders = resource.metadata.funding_agencies.all()
                all_funder_names_matched = True
                for funder in funders:
                    if not check_funder_name(funder.agency_name):
                        print(f"Resource:{res_id} has unknown funder name: {funder.agency_name}")
                        all_funder_names_matched = False
                if all_funder_names_matched:
                    print(f"Resource:{res_id} has all funder names matched")
        else:
            # check all published resources
            res_count = BaseResource.objects.filter(raccess__published=True).count()
            print(f"TOTAL PUBLISHED RESOURCES TO CHECK FOR FUNDER NAMES: {res_count}")
            print("=" * 100)
            res_counter = 0
            for resource in BaseResource.objects.filter(raccess__published=True):
                res_counter += 1
                resource = resource.get_content_model()
                funders = resource.metadata.funding_agencies.all()
                all_funder_names_matched = True
                for funder in funders:
                    if not check_funder_name(funder.agency_name):
                        print(f"{res_counter}. Resource:{resource.short_id} has unknown funder "
                              f"name: {funder.agency_name}")
                        all_funder_names_matched = False
                if all_funder_names_matched:
                    print(f"{res_counter}. Resource:{resource.short_id} has all funder names matched")
