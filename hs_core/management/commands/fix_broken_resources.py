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


VACUUM = [
    '094da7d9400f493fb1e412df015e17a4',
    # 'aff4e6dfc09a4070ac15a6ec0741fd02',
    # '5e80dd7cbaf04a5e98d850609c7e534b',
    # '325b21d55b2c49658a91944fabd896cf',
    # '9e5e99125d1646c69dde9fc43e137667',
    # '3ebf244bd2084cfaa68b83b7f91e9587',
    # '6aa75450ee2744cdb34ed8dde929a84a',
    # '887180409e4545018c8372f0bd6f8ff3',
    # '4a5bb3a976004f0ea63991323335b170',
    # 'ecb77926c2484e068f28acda434f8772',
    # '40655b4fc21142d090a5a4b835c14220',
    # '1846b79a648a4088aad987cc7241656f',
    # '94bcad20fbfb4c44ac7f98a0fdfa5e79',
    # 'a22bbdfb431c44a68959534c94e96392',
    # 'bc16655330b64bcaa366d464b00e45f0',
    # '2e9db97be020401c9aa03017cb7ee505',
    # 'c3ecee31a0c64490bf6a2fcb4841cee4',
    # 'a56608d8948c43fdb302e1438cf09169',
    # '878093a81b284ac8a4f65948b1c597a2',
    # 'e81b1fb3cb5a49538d6c2ad3077b7b71',
    # 'cdc6292fbee24dfd9810da7696a40dcf'
]


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        print("FIX ALL AFFECTED RESOURCES")

        for rid in VACUUM:  # delete all non-matching IDS
            r = get_resource_by_shortkey(rid)
            r.check_irods_files(echo_errors=True, log_errors=False, return_errors=False,
                                clean_irods=True, clean_django=True, sync_ispublic=True)
            resource_modified(r, r.creator)
            # Do a redundant check to ensure that cleaning worked.
            r.check_irods_files(echo_errors=True, log_errors=False, return_errors=False)
