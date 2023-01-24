from django.core.management.base import BaseCommand
from hs_core.hydroshare import hs_requests
import requests

# This code checks an externally valid URI by querying Nginx directly.
# It requires a login name and password for many kinds of queries.
# syntax ./hsctl managepy check_uri http://www.hydroshare.org --login=foo --password=bar
# Note that this redirects the test to hit the internal Nginx server, rather than django.
# Thus www.hydroshare.org actually maps to the Nginx docker container.
# The output of this is stored in the tmp directory of hydroshare


def check_uri(uri, options):
    """ try to download a URL with specific privileges """
    print("original url is {}".format(uri))
    if options['login'] and options['password']:
        r = hs_requests.get(uri, verify=False, stream=True,
                            auth=requests.auth.HTTPBasicAuth(options['login'], options['password']))
    else:
        r = hs_requests.get(uri, verify=False, stream=True)

    print("localized url is {}".format(str(r.url)))
    print("status code is {}".format(str(r.status_code)))
    for i in r.headers:
        print("{} is {}".format(i, r.headers[i]))
    file = 'tmp/check_uri_output'
    if 'Content-Disposition' in r.headers and \
       '; ' in r.headers['Content-Disposition']:
        filename = r.headers['Content-Disposition'].split('; ')[1].split('=')[1].strip('"')
        print("filename is {}".format(filename))
        if '.' in filename:
            extension = filename.split('.')
            extension = extension[len(extension) - 1]
            if extension != "":
                print("extension is .{}".format(extension))
                file = file + '.' + extension
    with open(file, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    print("query complete: output in {}".format(file))


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
            help='HydroShare password for login'
        )

    def handle(self, *args, **options):

        # disable verbose warnings about not verifying ssl
        requests.packages.urllib3.disable_warnings()

        # only respond to a single URI
        if len(options['uris']) == 0:  # an array of uris to check.
            print("no URI specified")
        elif len(options['uris']) > 1:
            print("too many URIs specified")
        uri = options['uris'][0]
        check_uri(uri, options)
