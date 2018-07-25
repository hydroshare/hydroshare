"""This does a comprehensive test of a resource.

This checks:
* IRODS files
* IRODS AVU values
* Existence of Logical files

Notes:
* By default, this script prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_core.models import BaseResource
from hs_core.hydroshare import get_resource_by_shortkey, group_from_id

def check_access(rid, options): 
    if not options['group'] and not options['user']: 
        resource = get_resource_by_shortkey(rid)
        print("ewaouexw {}".format(resource.short_id))
        for u in User.objects.filter(u2urp__resource=resource): 
            print("    user {}".format(u.username))
        for g in Group.objects.filter(g2grp__resource=resource): 
            print("    group {}".format(g.name))
            for u in User.objects.filter(u2ugp__group=g): 
                print("   group {} has memeber {}".format(g.name, u.username) )
    elif options['group']: 
        group = Group.objects.get(name=rid)
        print("group {}:".format(group.name))
        for u in User.objects.filter(u2ugp__group=group): 
            print("   user {}".format(u.username))
        for r in BaseResource.objects.filter(r2grp__group=group): 
            print("   resource {}".format(r.short_id))
    elif options['user']: 
        user = User.objects.get(username=rid)
        print("user {}:".format(user.username))
        for g in Group.objects.filter(g2ugp__user=user): 
            print("   group {}".format(g.name))
        for r in BaseResource.objects.filter(r2urp__user=user): 
            print("   resource {}".format(r.short_id))

class Command(BaseCommand):
    help = "Print results of testing resource integrity."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--group',
            action='store_true',  # True for presence, False for absence
            dest='group',         # value is options['group']
            help='show group access',
        )
        parser.add_argument(
            '--user',
            action='store_true',  # True for presence, False for absence
            dest='user',          # value is options['user']
            help='show user access',
        )

    def handle(self, *args, **options):
        if len(options['ids']) > 0:  # an array of resource short_id to check.
            for rid in options['ids']:
                check_access(rid, options)
        else:
            if not options['group'] and not options['user']: 
                for r in BaseResource.objects.all():
                    check_access(r.short_id, options)
            elif options['group']: 
                for g in Group.objects.all(): 
                    check_access(g.name, options) 
            else: 
                for u in User.objects.all(): 
                    check_access(u.username, options) 
