# -*- coding: utf-8 -*-

"""
Fix broken resources found in 1.10.0 migration.
This script should be run only once.
It performs resource-specific actions:
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
from django.conf import settings
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.hydroshare.utils import resource_modified
from hs_core.models import BaseResource
from django_irods.icommands import SessionException
from hs_core.hydroshare.resource import delete_resource

from hs_core.management.commands.ingest_irods_files import ingest_irods_files

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

CORRUPTED = [
    '49361c4e569e46eb9f2123594caf5804',
    'd3dcb1744be5478eb1edee95839c3463',
    'a28da53a49bb42d3bff9a50f0af387f1',
    '9daebf7ed6344a23a4c13a2ff36081c1',
    '37594b5bba544e14905dc0f8257c874f',
    '0b828da8c0b24ab786dee74b6f2eabf7',
    '1a664ae2fd4744f6aeb060de46a8739f',
    'fbde31db496b450e83db20862c89a11c',
    'c43944f0e2f84f2dbd8b9e05e5f6314a',
    'd2683f86f18d4c1cbf58a619086c3268',
    'a184d5f080c84054ab715c46162232fc',
    'f196399316764d169fbe4f140a70f1f5',
    '0909e74dfc734397afd1abafecc4315a',
    '30c49e486f2c45648698e20778b751a6'
]

DELETE = [
    '8fd42ad1d86f495a914e7ce9be21bbce'
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

        for rid in DELETE:  # delete whole resource for unmanageable resources
            try:
                resource = BaseResource.objects.get(short_id=rid)
                print("DELETING {} FROM DJANGO ({} files)"
                      .format(rid, str(resource.files.all().count())))
                delete_resource(rid)
            except BaseResource.DoesNotExist:
                print("RESOURCE {} NOT FOUND IN DJANGO".format(rid))

        print("REPAIR BROKEN NETCDF RESOURCES")

        for r in BaseResource.objects.filter(resource_type='NetcdfResource'):
            if r.is_federated and not settings.REMOTE_USE_IRODS:
                print("INFO: skipping repair of federated resource {} in unfederated mode"
                      .format(r.short_id))
            else:

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
                        print("resource {} ({}) not found in iRODS".format(r.short_id, r.root_path))
        print("REMOVE '/./' FROM PATHS")
        for rid in CORRUPTED:
            r = get_resource_by_shortkey(rid)
            if r.is_federated and not settings.REMOTE_USE_IRODS:
                print("INFO: skipping repair of federated resource {} in unfederated mode"
                      .format(r.short_id))
            else:
                istorage = r.get_irods_storage()
                print("INFO: checking {} for /./ ({} files)"
                      .format(r.short_id, str(r.files.all().count())))
                if istorage.exists(r.root_path):
                    for f in r.files.all():
                        if '/./' in f.storage_path:
                            cleaned = f.storage_path
                            cleaned = cleaned.replace('/./', '/')
                            print("INFO: replacing path {} with {}"
                                  .format(f.storage_path, cleaned))
                            f.set_storage_path(cleaned)
                else:
                    print("INFO: skipping resource {} with no files".format(rid))

        print("CHECK FOR FILE INCLUSION IN DJANGO")
        for rid in CORRUPTED:
            r = get_resource_by_shortkey(rid)
            if r.is_federated and not settings.REMOTE_USE_IRODS:
                print("INFO: skipping repair of federated resource {} in unfederated mode"
                      .format(r.short_id))
            else:
                istorage = r.get_irods_storage()
                print("INFO: checking {} for new files ({} files)"
                      .format(r.short_id, str(r.files.all().count())))
                if istorage.exists(r.root_path):
                    if r.resource_type == 'CompositeResource' or \
                       r.resource_type == 'GenericResource':
                        print(("LOOKING FOR UNREGISTERED IRODS FILES FOR RESOURCE {}" +
                               " (current files {})")
                              .format(r.short_id, str(r.files.all().count())))
                        ingest_irods_files(r,
                                           None,
                                           stop_on_error=False,
                                           echo_errors=True,
                                           log_errors=False,
                                           return_errors=False)
                else:
                    print("resource {} has type {}: skipping"
                          .format(r.short_id, r.resource_type))

        print("REPAIR ISPUBLIC AVUS")
        for r in BaseResource.objects.all():
            if r.is_federated and not settings.REMOTE_USE_IRODS:
                print("INFO: skipping repair of federated resource {} in unfederated mode"
                      .format(r.short_id))
            else:
                istorage = r.get_irods_storage()
                if istorage.exists(r.root_path):
                    pub = r.getAVU('isPublic')
                    if pub != r.raccess.public:
                        print("INFO: resource {}: isPublic is {}, public is {} (REPAIRING)"
                              .format(r.short_id, pub, r.raccess.public))
                        r.setAVU('isPublic', r.raccess.public)
                else:
                    print("ERROR: non-existent collection {} ({})".format(r.short_id, r.root_path))
