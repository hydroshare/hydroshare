from django.core.management.base import BaseCommand
from hs_core.hydroshare import hs_requests
import requests


def check_uri(uri, options):
    """ try to download a URL with specific privileges """
    print("uri to check is {}".format(uri))
    if options['login'] and options['password']:
        r = hs_requests.get(uri, verify=False, stream=True,
                            auth=requests.auth.HTTPBasicAuth(options['login'], options['password']))
    else:
        r = hs_requests.get(uri, verify=False, stream=True)

    print("status is {}".format(str(r.status_code)))
    filename = 'tmp/test_check_uri'
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)


class Command(BaseCommand):
    help = "Check response of an arbitrary hydroshare URI"

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('uris', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--login',
            default='admin',
            dest='login',  # value is options['login']
            help='HydroShare login name'
        )

        parser.add_argument(
            '--password',
            default=None,
            dest='password',  # value is options['password']
            help='HydroShare password'
        )

    def handle(self, *args, **options):

        # disable verbose warnings about not verifying ssl
        requests.packages.urllib3.disable_warnings()

        if len(options['uris']) > 0:  # an array of uris to check.
            for uri in options['uris']:
                check_uri(uri, options)
        else:
            print("No uris given.")
