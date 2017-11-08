from django.core.management.base import BaseCommand

from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes
from django_irods.icommands import SessionException


class Command(BaseCommand):
    """
    This adds the quotaUserName AVU to iRODS from the resource database as needed.
    It also -- additionally -- resets the quota system for existing quotaUserName AVUs.
    """
    help = "Add quotaUserName AVU to all resources in iRODS as needed"

    def handle(self, *args, **options):
        resources = BaseResource.objects.all()
        for res in resources:
            try:
                if not res.get_quota_holder():
                    # if quota_holder is not set for the resource, set it to resource's creator
                    # for some resource, for some reason, the creator of the resource is not the
                    # owner, hence not allowed to be set as quota holder. This is an artifact that
                    # needs to be patched since the person who initially uploaded resource should
                    # be the owner of the resource. Hence, add resource creator to owner list if
                    # creator is not already in the owner list
                    if not res.creator.uaccess.owns_resource(res):
                        first_owner = res.raccess.owners.first()
                        if first_owner:
                            first_owner.uaccess.share_resource_with_user(res, res.creator,
                                                                         PrivilegeCodes.OWNER)
                        else:
                            # this resource has no owner, which should never be allowed and never
                            # happen
                            print res.short_id + ' does not have an owner'
                            continue
                    res.set_quota_holder(res.creator, res.creator)

                # Now reset the quota system by setting the AVU 'resetQuotaDir' to anything
                istorage = res.get_irods_storage()
                # Add a specific AVU to invoke quota recalculation
                istorage.session.run("imeta", None, 'set', '-C', res.root_path,
                                     'resetQuotaDir', '0')
                # Now remove that AVU to clean up; this is not part of the resource API
                istorage.session.run("imeta", None, 'rm', '-C', res.root_path,
                                     'resetQuotaDir', '0')

            except SessionException as ex:
                # this is needed for migration testing where some resources copied from www
                # for testing do not exist in the iRODS backend, hence need to skip these
                # test artifects
                print(res.short_id + ' raised SessionException when setting quota holder: ' +
                      ex.stderr)
                continue
            except AttributeError as ex:
                # when federation is not set up correctly, istorage does not have a session
                # attribute, hence raise AttributeError - ignore for testing and it should not
                # happen in production where federation is set up properly
                print(res.short_id + ' raised AttributeError when setting quota holder: ' +
                      ex.message)
                continue
            except ValueError as ex:
                # when federation is not set up correctly, istorage does not have a session
                # attribute, hence raise AttributeError - ignore for testing and it should not
                # happen in production where federation is set up properly
                print(res.short_id + ' raised ValueError when setting quota holder: ' +
                      ex.message)
                continue
