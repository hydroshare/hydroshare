# -*- coding: utf-8 -*-

"""
Fix broken resources found in 1.10.0 migration.
This script should be run only once.
It performs resource-specific actions.
094da7d9400f493fb1e412df015e17a4 Delete files in iRODS that are not in Django (duplicates)
aff4e6dfc09a4070ac15a6ec0741fd02 Delete files in Django that are not in Irods (failed upload)
5e80dd7cbaf04a5e98d850609c7e534b Delete files in Django that are not in Irods (failed upload)
325b21d55b2c49658a91944fabd896cf Delete files in Django that are not in Irods (failed upload)
9e5e99125d1646c69dde9fc43e137667 Delete files in Django that are not in Irods (failed upload)
3ebf244bd2084cfaa68b83b7f91e9587 Delete files in Django that are not in Irods (failed upload)
6aa75450ee2744cdb34ed8dde929a84a Delete files in Django that are not in Irods (failed upload)
887180409e4545018c8372f0bd6f8ff3 Delete files in Django that are not in Irods (failed upload)
4a5bb3a976004f0ea63991323335b170 Delete files in Django that are not in Irods (failed upload)
ecb77926c2484e068f28acda434f8772 Delete files in Django that are not in Irods (failed upload)
40655b4fc21142d090a5a4b835c14220 Delete files in Django that are not in Irods (failed upload)
1846b79a648a4088aad987cc7241656f Delete files in Django that are not in Irods (failed upload)
94bcad20fbfb4c44ac7f98a0fdfa5e79 Delete files in Django that are not in Irods (failed upload)
a22bbdfb431c44a68959534c94e96392 Delete files in Django that are not in Irods (failed upload)
bc16655330b64bcaa366d464b00e45f0 Delete files in Django that are not in Irods (failed upload)
2e9db97be020401c9aa03017cb7ee505 Delete files in Django that are not in Irods (failed upload)
c3ecee31a0c64490bf6a2fcb4841cee4 Delete files in Django that are not in Irods (failed upload)
a56608d8948c43fdb302e1438cf09169 Delete files in Django that are not in Irods (failed upload)
878093a81b284ac8a4f65948b1c597a2 Delete files in Django that are not in Irods (failed upload)
e81b1fb3cb5a49538d6c2ad3077b7b71 Delete unreferenced files on both sides.
cdc6292fbee24dfd9810da7696a40dcf Delete unreferenced files on both sides.
"""

from django.core.management.base import BaseCommand
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.hydroshare.utils import resource_modified
from hs_core.models import BaseResource
from django_irods.icommands import SessionException

# These should be cleaned up by deleting extra files
VACUUM = [
    '094da7d9400f493fb1e412df015e17a4',
    'aff4e6dfc09a4070ac15a6ec0741fd02',
    '5e80dd7cbaf04a5e98d850609c7e534b',
    '325b21d55b2c49658a91944fabd896cf',
    '9e5e99125d1646c69dde9fc43e137667',
    '3ebf244bd2084cfaa68b83b7f91e9587',
    '6aa75450ee2744cdb34ed8dde929a84a',
    '887180409e4545018c8372f0bd6f8ff3',
    '4a5bb3a976004f0ea63991323335b170',
    'ecb77926c2484e068f28acda434f8772',
    '40655b4fc21142d090a5a4b835c14220',
    '1846b79a648a4088aad987cc7241656f',
    '94bcad20fbfb4c44ac7f98a0fdfa5e79',
    'a22bbdfb431c44a68959534c94e96392',
    'bc16655330b64bcaa366d464b00e45f0',
    '2e9db97be020401c9aa03017cb7ee505',
    'c3ecee31a0c64490bf6a2fcb4841cee4',
    'a56608d8948c43fdb302e1438cf09169',
    '878093a81b284ac8a4f65948b1c597a2',
    'e81b1fb3cb5a49538d6c2ad3077b7b71',
    'cdc6292fbee24dfd9810da7696a40dcf'
]

# The AVUs should be fixed for these
PUBLIC = [ 
    '0359cab7d93f403ba6ee8726cff74f8a',
    '040dfdc5e0684a40bd13c0259e971bb7',
    '05a29e4ddffd42b88f482bd5be46e88d',
    '0ae62cfb9f3347d29c8211564f8db515',
    '0b7dcbc238c947239a6f949abec869db',
    '0cb834d7635943e98d770e9df0c522fe',
    '126bb28f05224636a8bc8b3d1bdad6b5',
    '17c732b4ec924f54ba73aa77497d8354',
    '1c14485cf5f445f99564c847bf7b9cf5',
    '1d78964652034876b1c190647b21a77d',
    '22c6c32608694cf38746cd665f255957',
    '2443f9ff1217412f992b27f89942f87e',
    '2ccee33680d64c138762ae8928810749',
    '2d07c0d7695149f39c233bf3215ccd4a',
    '310621bbccf24c958854632b2b26ad45',
    '3118410c99bd4a86a91407e0a3d16e9a',
    '31ee40f4726546f5ab9ca2e3a8e3d557',
    '31f35199a2e548e29786182fbb3e2941',
    '3202e694a05143f1a9ba30f8bc615cab',
    '39127f7285d548e181a81ca5a789fb79',
    '46c1b0f6c16c4ae1b71298cda7cfc0ab',
    '500952f35e0b456f984835d306dfa4a3',
    '53bab1bbcd544ad78e45443da7246fe4',
    '57d8a925efbd4c33ac074297ade37ad8',
    '6805aaed7a424d8f9971ac404ecd1da3',
    '68fe2d39f40e4bf5bdfde6526259dc10',
    '6a38890c0ce24c22badf89cb1da6be79',
    '6db094fb5e5e4fae9a0bd047263d9ebc',
    '6dbb0dfb8f3a498881e4de428cb1587c',
    '7246f52a298848e4830249e8b626a904',
    '7ccd6a6a8341443a9d9396ca4502ad22',
    '85d16c91c20f450f8aecb460c8cfb947',
    '877bf9ed9e66468cadddb229838a9ced',
    '89125e9a3af544eab2479b7a974100ba',
    '895cc2fc795f4a63ab35c291d39977dc',
    '89e8df6d8b134238b30225df1a2cf454'
]


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        print("FIX BROKEN RESOURCES")

        for rid in VACUUM:  # delete all non-matching IDS
            r = get_resource_by_shortkey(rid)
            r.check_irods_files(echo_errors=True, log_errors=False, return_errors=False,
                                clean_irods=True, clean_django=True, sync_ispublic=True)
            resource_modified(r, r.creator)
            # Do a redundant check to ensure that cleaning worked.
            r.check_irods_files(echo_errors=True, log_errors=False, return_errors=False)

        print("REPAIR BROKEN NETCDF RESOURCES")

        for r in BaseResource.objects.filter(resource_type='NetcdfResource'):
            istorage = r.get_irods_storage()
            for f in r.files.all():
                try:
                    if f.short_path.endswith('.txt') and not istorage.exists(f.storage_path):
                        print("found broken NetCDF resource {}".format(r.short_id))
                        files = istorage.listdir(r.file_path)[1]
                        for g in files:
                            if g.endswith('.txt'):
                                print("in {}, changing short path {} to {}"
                                      .format(r.short_id, f.short_path, g))
                                f.set_short_path(g)
                                # Now check for file integrity afterward
                                r.check_irods_files(echo_errors=True, log_errors=False,
                                                    return_errors=False, clean_irods=False,
                                                    clean_django=False, sync_ispublic=True)
                                break
                except SessionException:
                    print("resource {} not found in iRODS".format(r.short_id))

        print("REPAIR ISPUBLIC AVUS")
        for rid in PUBLIC:  # resources with unsynchronized AVUs
            r = get_resource_by_shortkey(rid)
            r.check_irods_files(echo_errors=True, log_errors=False, return_errors=False,
                                clean_irods=False, clean_django=False, sync_ispublic=True)
