"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import check_irods_files


def debug_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    irods_issues, irods_errors, _, _ = check_irods_files(resource, log_errors=False, return_errors=True)

    print("resource: {}".format(short_id))
    print("resource type: {}".format(resource.resource_type))
    print("resource creator: {} {}".format(resource.creator.first_name, resource.creator.last_name))
    print("resource irods bag modified: {}".format(str(resource.getAVU('bag_modified'))))
    print("resource irods isPublic: {}".format(str(resource.getAVU('isPublic'))))
    print("resource irods resourceType: {}".format(str(resource.getAVU('resourceType'))))
    print("resource quota holder: {}".format(str(resource.quota_holder.username)))
    if irods_errors:
        print("iRODS errors:")
        for e in irods_issues:
            print("    {}".format(e))
    else:
        print("No iRODS errors")

    if resource.resource_type == 'CompositeResource':
        print("Resource file logical files:")
        for res_file in resource.files.all():
            if res_file.has_logical_file:
                print(("    {} logical file {} is [{}]".format(res_file.short_path,
                                                               str(type(res_file.logical_file)),
                                                               str(res_file.logical_file.id))))

    # context = {
    #     'shortkey': shortkey,
    #     'creator': resource.creator,
    #     'resource': resource,
    #     'raccess': resource.raccess,
    #     'owners': resource.raccess.owners,
    #     'editors': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE),
    #     'viewers': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
    #     'public_AVU': resource.getAVU('isPublic'),
    #     'type_AVU': resource.getAVU('resourceType'),
    #     'modified_AVU': resource.getAVU('bag_modified'),
    #     'quota_AVU': resource.getAVU('quotaUserName'),
    #     'irods_issues': irods_issues,
    #     'irods_errors': irods_errors,
    # }


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                debug_resource(rid)
        else:
            print("No resources to check.")
